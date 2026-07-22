from sqlalchemy.orm import Session
from app.models.hospital import Hospital
from app.models.hospital_request import HospitalRequest
from app.schemas.hospital_request import HospitalRequestCreate, HospitalRequestResponse
import uuid
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

class HospitalService:

    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        """SMTP သုံးပြီး Email ပို့ပေးမယ်"""
        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False

    @staticmethod
    def create_request(db: Session, data: HospitalRequestCreate) -> HospitalRequestResponse:
        """ဆေးရုံအသစ် Register Request ကို PENDING အနေနဲ့ သိမ်းမယ်"""
        new_request = HospitalRequest(
            hospital_name=data.hospital_name,
            address=data.address,
            contact_email=data.contact_email,
            status="pending"
        )
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        return HospitalRequestResponse(
            id=str(new_request.id),
            hospital_name=new_request.hospital_name,
            address=new_request.address,
            contact_email=new_request.contact_email,
            status=new_request.status,
            rejection_reason=new_request.rejection_reason,
            hospital_id=str(new_request.hospital_id) if new_request.hospital_id else None,
            requested_at=new_request.requested_at,
            processed_at=new_request.processed_at
        )

    @staticmethod
    def get_pending_requests(db: Session) -> list[HospitalRequestResponse]:
        """PENDING Status ရှိတဲ့ Request အားလုံးကို ဆွဲယူမယ်"""
        requests = db.query(HospitalRequest).filter(HospitalRequest.status == "pending").order_by(HospitalRequest.requested_at).all()
        
        return [
            HospitalRequestResponse(
                id=str(req.id),
                hospital_name=req.hospital_name,
                address=req.address,
                contact_email=req.contact_email,
                status=req.status,
                rejection_reason=req.rejection_reason,
                hospital_id=str(req.hospital_id) if req.hospital_id else None,
                requested_at=req.requested_at,
                processed_at=req.processed_at
            )
            for req in requests
        ]

    @staticmethod
    def approve_request(db: Session, request_id: str) -> tuple[bool, str]:
        """Request ကို Approve လုပ်ပြီး Hospital အသစ် Create လုပ်မယ်"""
        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return False, "Invalid request ID format"
            
        req = db.query(HospitalRequest).filter(HospitalRequest.id == request_uuid).first()
        if not req:
            return False, "Request not found"
        if req.status != "pending":
            return False, f"Request is already {req.status}"

        # ၁။ Hospital အသစ် Create လုပ်
        new_hospital = Hospital(
            name=req.hospital_name,
            api_key=str(uuid.uuid4())
        )
        db.add(new_hospital)
        db.flush()

        # ၂။ Request Status ကို Approved ပြောင်း
        req.status = "approved"
        req.processed_at = datetime.utcnow()
        req.hospital_id = new_hospital.id

        db.commit()
        db.refresh(new_hospital)

        # ၃။ API Key ကို Email ပို့မယ်
        email_body = f"""
        မင်္ဂလာပါ {req.hospital_name},

        သင့်ဆေးရုံအတွက် Blood Bank System မှ Registration ကို Global Admin မှ အတည်ပြုပေးလိုက်ပါပြီ။
        အောက်ပါ API Key ကို သင့် Local Server ၏ .env ဖိုင်ထဲတွင် ထည့်သွင်းပြီး Server ကို Restart လုပ်ပါ။

        HOSPITAL_ID={new_hospital.id}
        HOSPITAL_API_KEY={new_hospital.api_key}

        ကျေးဇူးပြု၍ ဤ Key ကို လုံခြုံစွာ သိမ်းဆည်းထားပါ။
        Blood Bank Global System
        """

        HospitalService.send_email(
            to_email=req.contact_email,
            subject="Your Hospital Registration is Approved - API Key",
            body=email_body
        )

        return True, "Hospital approved and API key sent via email"

    @staticmethod
    def reject_request(db: Session, request_id: str, reason: str) -> tuple[bool, str]:
        """Request ကို Reject လုပ်မယ်"""
        try:
            request_uuid = uuid.UUID(request_id)
        except ValueError:
            return False, "Invalid request ID format"
            
        req = db.query(HospitalRequest).filter(HospitalRequest.id == request_uuid).first()
        if not req:
            return False, "Request not found"
        if req.status != "pending":
            return False, f"Request is already {req.status}"

        req.status = "rejected"
        req.rejection_reason = reason
        req.processed_at = datetime.utcnow()
        db.commit()
        
        return True, "Request rejected"