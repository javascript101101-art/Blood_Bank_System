// ============================================
// Donor Management (UPDATED with Traceability History)
// ============================================
let editingDonorId = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadDonors();

    const modal = document.getElementById('donorModal');
    const addBtn = document.getElementById('addDonorBtn');
    const closeBtn = document.querySelector('.close');

    if (addBtn) {
        addBtn.addEventListener('click', () => openDonorModal());
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', () => closeDonorModal());
    }

    window.addEventListener('click', (e) => {
        if (e.target === modal) closeDonorModal();
    });

    const form = document.getElementById('donorForm');
    if (form) {
        form.addEventListener('submit', handleDonorSubmit);
    }
});

// ============================================
// Load Donors
// ============================================
async function loadDonors() {
    const tbody = document.getElementById('donorsBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="6">Loading...</td></tr>';

    try {
        const result = await apiRequest('/donors/', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6">No donors found.</td></tr>';
                return;
            }
            
            tbody.innerHTML = result.data.map(donor => `
                <tr>
                    <td><strong>${donor.name}</strong></td>
                    <td>${donor.dob ? formatDate(donor.dob) : '-'}</td>
                    <td><span class="badge">${donor.blood_group}</span></td>
                    <td>${donor.rh_factor}</td>
                    <td>${donor.contact_phone || '-'}</td>
                    <td style="text-align: center;">
                        <!-- 🟢 သွေးလှူဒါန်းမှု မှတ်တမ်းကြည့်ရန် 📜 ခလုတ်အသစ် -->
                        <button class="btn btn-info btn-sm" onclick="openDonorHistory('${donor.id}', '${donor.name}')" title="သွေးလှူဒါန်းမှု မှတ်တမ်းကြည့်ရန်">📜</button>
                        <button class="btn btn-warning btn-sm" onclick="editDonor('${donor.id}')">✏️</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteDonor('${donor.id}')">🗑️</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6">Error loading donors.</td></tr>';
        console.error('Error loading donors:', error);
    }
}

// ============================================
// 🟢 Open Donor History Modal (Traceability)
// ============================================
async function openDonorHistory(donorId, donorName) {
    const historyModal = document.getElementById('donorHistoryModal');
    const nameEl = document.getElementById('historyDonorName');
    const tbody = document.getElementById('donorHistoryBody');

    nameEl.textContent = donorName;
    tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding: 15px;">မှတ်တမ်းများ ရယူနေသည်...</td></tr>';
    
    historyModal.classList.add('show');

    try {
        const result = await apiRequest(`/donors/${donorId}/history`, { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding: 15px;">ဤအလှူရှင်တွင် လှူဒါန်းမှု မှတ်တမ်းမရှိသေးပါ။</td></tr>';
                return;
            }

            tbody.innerHTML = result.data.map(item => {
                const componentDisplay = (item.blood_component || 'Whole_Blood').replace('_', ' ').toUpperCase();
                return `
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 10px;"><span class="badge" style="background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1;">${componentDisplay}</span></td>
                        <td style="padding: 10px; font-weight: bold;">${item.quantity_ml} ml</td>
                        <td style="padding: 10px;">${formatDate(item.expiry_date)}</td>
                        <td style="padding: 10px;"><span class="status-badge status-${item.status.toLowerCase()}">${item.status}</span></td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding: 15px; color: red;">မှတ်တမ်းရယူရာတွင် အမှားအယွင်းရှိသည်။</td></tr>';
        }
    } catch (error) {
        console.error('Error loading donor history:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding: 15px; color: red;">Network error. Please try again.</td></tr>';
    }
}

// ============================================
// Open/Close Modal
// ============================================
function openDonorModal(donorData = null) {
    const modal = document.getElementById('donorModal');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('donorForm');
    const errorEl = document.getElementById('donorFormError');
    
    errorEl.style.display = 'none';
    form.reset();
    editingDonorId = null;

    if (donorData) {
        title.textContent = 'Edit Donor';
        document.getElementById('donorId').value = donorData.id;
        document.getElementById('donorName').value = donorData.name;
        document.getElementById('donorDob').value = donorData.dob || '';
        document.getElementById('donorBloodGroup').value = donorData.blood_group;
        document.getElementById('donorRhFactor').value = donorData.rh_factor;
        document.getElementById('donorPhone').value = donorData.contact_phone || '';
        document.getElementById('donorEmail').value = donorData.email || '';
        document.getElementById('donorLastDonation').value = donorData.last_donation_date || '';
        document.getElementById('donorQuantity').value = donorData.donation_quantity || '';
        
        document.getElementById('donorHemoglobin').value = donorData.hemoglobin_level || '';
        document.getElementById('donorTemperature').value = donorData.temperature || '';
        document.getElementById('donorBP').value = donorData.blood_pressure || '';

        editingDonorId = donorData.id;
    } else {
        title.textContent = 'Add New Donor';
        document.getElementById('donorQuantity').value = '';
    }

    modal.classList.add('show');
}

function closeDonorModal() {
    document.getElementById('donorModal').classList.remove('show');
    document.getElementById('donorForm').reset();
    document.getElementById('donorFormError').style.display = 'none';
    editingDonorId = null;
}

// ============================================
// Edit Donor
// ============================================
async function editDonor(id) {
    try {
        const result = await apiRequest(`/donors/${id}`, { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            openDonorModal(result.data);
        }
    } catch (error) {
        alert('Error loading donor data.');
    }
}

// ============================================
// Delete Donor
// ============================================
async function deleteDonor(id) {
    if (!confirm('Are you sure you want to delete this donor?')) return;

    try {
        const result = await apiRequest(`/donors/${id}`, { method: 'DELETE' });
        if (result && (result.status === 204 || result.status === 200)) {
            loadDonors();
        } else {
            alert('Error deleting donor.');
        }
    } catch (error) {
        alert('Network error. Please check your connection.');
    }
}

// ============================================
// Handle Form Submit
// ============================================
async function handleDonorSubmit(e) {
    e.preventDefault();
    
    const errorEl = document.getElementById('donorFormError');
    errorEl.style.display = 'none';

    const quantity = parseInt(document.getElementById('donorQuantity').value);
    if (isNaN(quantity) || quantity < 100 || quantity > 600) {
        errorEl.textContent = 'Donation quantity must be between 100ml and 600ml.';
        errorEl.style.display = 'block';
        return;
    }

    const hemoglobin = parseFloat(document.getElementById('donorHemoglobin').value);
    const temperature = parseFloat(document.getElementById('donorTemperature').value);
    const bp = document.getElementById('donorBP').value;

    const donorData = {
        name: document.getElementById('donorName').value,
        dob: document.getElementById('donorDob').value || null,
        blood_group: document.getElementById('donorBloodGroup').value,
        rh_factor: document.getElementById('donorRhFactor').value,
        contact_phone: document.getElementById('donorPhone').value || null,
        email: document.getElementById('donorEmail').value || null,
        last_donation_date: document.getElementById('donorLastDonation').value || null,
        donation_quantity: quantity,
        hemoglobin_level: isNaN(hemoglobin) ? null : hemoglobin,
        temperature: isNaN(temperature) ? null : temperature,
        blood_pressure: bp || null
    };

    try {
        let result;
        if (editingDonorId) {
            result = await apiRequest(`/donors/${editingDonorId}`, {
                method: 'PUT',
                body: JSON.stringify(donorData)
            });
        } else {
            result = await apiRequest('/donors/', {
                method: 'POST',
                body: JSON.stringify(donorData)
            });
        }

        if (result && (result.status === 201 || result.status === 200)) {
            closeDonorModal();
            loadDonors();
        } else {
            errorEl.textContent = result?.data?.detail || 'Error saving donor.';
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.style.display = 'block';
    }
}

// ============================================
// Utility Functions
// ============================================
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}