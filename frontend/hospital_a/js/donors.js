// ============================================
// Donor Management
// ============================================
let editingDonorId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Check authentication
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadDonors();

    // Modal events
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

    // Form submit
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
                    <td>
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
        editingDonorId = donorData.id;
    } else {
        title.textContent = 'Add New Donor';
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
// Edit Donor (called from table)
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
// ============================================
// Delete Donor (FIXED)
// ============================================
async function deleteDonor(id) {
    if (!confirm('Are you sure you want to delete this donor?')) return;

    try {
        const result = await apiRequest(`/donors/${id}`, { method: 'DELETE' });
        
        // 204 No Content နဲ့ 200 OK ကို အောင်မြင်တယ်လို့ သတ်မှတ်ပါ
        if (result && (result.status === 204 || result.status === 200)) {
            // အောင်မြင်ပါက Table ကို Refresh လုပ်ပါ
            loadDonors();
            // Optional: Success message ပြရန်
            // alert('Donor deleted successfully!');
        } else {
            // အခြား Status တွေအတွက် Error ပြပါ
            const errorMsg = result?.data?.detail || 'Error deleting donor. Please try again.';
            alert(errorMsg);
        }
    } catch (error) {
        console.error('Delete error:', error);
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

    const donorData = {
        name: document.getElementById('donorName').value,
        dob: document.getElementById('donorDob').value || null,
        blood_group: document.getElementById('donorBloodGroup').value,
        rh_factor: document.getElementById('donorRhFactor').value,
        contact_phone: document.getElementById('donorPhone').value || null,
        email: document.getElementById('donorEmail').value || null,
        last_donation_date: document.getElementById('donorLastDonation').value || null
    };

    try {
        let result;
        if (editingDonorId) {
            // Update
            result = await apiRequest(`/donors/${editingDonorId}`, {
                method: 'PUT',
                body: JSON.stringify(donorData)
            });
        } else {
            // Create
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