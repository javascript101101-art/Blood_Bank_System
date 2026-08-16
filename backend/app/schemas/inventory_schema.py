from pydantic import BaseModel, Field
from datetime import date, datetime
from uuid import UUID
from typing import Optional

class InventoryBase(BaseModel):
    blood_group: str = Field(..., pattern="^(A|B|AB|O)$")
    rh_factor: str = Field(..., pattern="^(Positive|Negative)$")
    quantity_ml: int = Field(..., ge=0)
    
    # 🆕 အလှူရှင်နှင့် ချိတ်ဆက်ရန် (Optional အနေဖြင့် လက်ခံမည်)
    donor_id: Optional[UUID] = None
    
    # 🟢 အသစ် - ဘယ် Request အတွက် သုံးလိုက်လဲဆိုတာ ခြေရာခံရန် (Vein-to-Vein Traceability)
    blood_request_id: Optional[UUID] = None
    
    # 🆕 သွေးအစိတ်အပိုင်း အမျိုးအစား (ဥပမာ - Red_Cells, Plasma, Platelets)
    blood_component: str = Field(..., pattern="^(Red_Cells|Plasma|Platelets|Whole_Blood|Processed)$")
    
    # 🆕 သိမ်းဆည်းရမည့် အပူချိန် (Backend မှ Auto ထည့်ပေးမည်ဖြစ်၍ Optional ထားပါသည်)
    storage_condition: Optional[str] = None
    
    # 🔄 Backend မှ Auto တွက်ပေးမည်ဖြစ်၍ Create လုပ်ချိန်တွင် Optional ဖြစ်ပါသည်
    expiry_date: Optional[date] = None
    
    # 🔄 Status များကို ပိုမိုစုံလင်စွာ ထည့်သွင်းထားပါသည်
    status: Optional[str] = Field("Available", pattern="^(Available|Expired|Quarantined|Discarded|Used|Processed)$")

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(InventoryBase):
    pass

class InventoryResponse(InventoryBase):
    id: UUID
    hospital_id: UUID
    expiry_date: date  # Database ထဲဝင်ပြီးပါက သေချာပေါက်ရှိမည်ဖြစ်၍ Response တွင် Required ဖြစ်ပါသည်
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ============================================
# 🆕 Component Splitting အတွက် Schema အသစ်
# ============================================
class InventorySplitRequest(BaseModel):
    red_cells_ml: Optional[int] = Field(0, ge=0, description="သွေးနီဥ ပမာဏ (ml)")
    plasma_ml: Optional[int] = Field(0, ge=0, description="သွေးရည်ကြည် ပမာဏ (ml)")
    platelets_ml: Optional[int] = Field(0, ge=0, description="သွေးဥမွှား ပမာဏ (ml)")