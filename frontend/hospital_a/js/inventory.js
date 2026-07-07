// ============================================
// Inventory Management
// ============================================
let editingInventoryId = null;

document.addEventListener('DOMContentLoaded', function() {
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }

    loadInventory();

    // Modal events
    const modal = document.getElementById('inventoryModal');
    const addBtn = document.getElementById('addInventoryBtn');
    const closeBtn = document.querySelector('.close');

    if (addBtn) addBtn.addEventListener('click', () => openInventoryModal());
    if (closeBtn) closeBtn.addEventListener('click', closeInventoryModal);

    window.addEventListener('click', (e) => {
        if (e.target === modal) closeInventoryModal();
    });

    // Form submit
    const form = document.getElementById('inventoryForm');
    if (form) form.addEventListener('submit', handleInventorySubmit);
});

// ============================================
// Load Inventory
// ============================================
async function loadInventory() {
    const tbody = document.getElementById('inventoryBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="6">Loading...</td></tr>';

    try {
        const result = await apiRequest('/inventory/', { method: 'GET' });
        
        if (result && result.status === 200 && result.data) {
            if (result.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6">No inventory records found.</td></tr>';
                return;
            }
            
            tbody.innerHTML = result.data.map(item => `
                <tr>
                    <td><strong>${item.blood_group}</strong></td>
                    <td>${item.rh_factor}</td>
                    <td>${item.quantity_ml}</td>
                    <td>${formatDate(item.expiry_date)}</td>
                    <td><span class="status-badge status-${item.status.toLowerCase()}">${item.status}</span></td>
                    <td>
                        <button class="btn btn-warning btn-sm" onclick="editInventory('${item.id}')">✏️</button>
                        <button class="btn btn-danger btn-sm" onclick="deleteInventory('${item.id}')">🗑️</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6">Error loading inventory.</td></tr>';
        console.error('Error loading inventory:', error);
    }
}

// ============================================
// Open/Close Modal
// ============================================
function openInventoryModal(inventoryData = null) {
    const modal = document.getElementById('inventoryModal');
    const title = document.getElementById('modalTitle');
    const form = document.getElementById('inventoryForm');
    const errorEl = document.getElementById('inventoryFormError');
    
    errorEl.style.display = 'none';
    form.reset();
    editingInventoryId = null;

    if (inventoryData) {
        title.textContent = 'Edit Inventory';
        document.getElementById('inventoryId').value = inventoryData.id;
        document.getElementById('invBloodGroup').value = inventoryData.blood_group;
        document.getElementById('invRhFactor').value = inventoryData.rh_factor;
        document.getElementById('invQuantity').value = inventoryData.quantity_ml;
        document.getElementById('invExpiryDate').value = inventoryData.expiry_date;
        document.getElementById('invStatus').value = inventoryData.status;
        editingInventoryId = inventoryData.id;
    } else {
        title.textContent = 'Add New Inventory';
        document.getElementById('invStatus').value = 'Available';
    }

    modal.classList.add('show');
}

function closeInventoryModal() {
    document.getElementById('inventoryModal').classList.remove('show');
    document.getElementById('inventoryForm').reset();
    document.getElementById('inventoryFormError').style.display = 'none';
    editingInventoryId = null;
}

// ============================================
// Edit Inventory
// ============================================
async function editInventory(id) {
    try {
        const result = await apiRequest(`/inventory/${id}`, { method: 'GET' });
        if (result && result.status === 200 && result.data) {
            openInventoryModal(result.data);
        }
    } catch (error) {
        alert('Error loading inventory data.');
    }
}

// ============================================
// Delete Inventory
// ============================================
async function deleteInventory(id) {
    if (!confirm('Are you sure you want to delete this inventory record?')) return;

    try {
        const result = await apiRequest(`/inventory/${id}`, { method: 'DELETE' });
        if (result && (result.status === 204 || result.status === 200)) {
            loadInventory();
        } else {
            alert('Error deleting inventory record.');
        }
    } catch (error) {
        alert('Network error. Please check your connection.');
    }
}

// ============================================
// Handle Form Submit
// ============================================
async function handleInventorySubmit(e) {
    e.preventDefault();
    
    const errorEl = document.getElementById('inventoryFormError');
    errorEl.style.display = 'none';

    const inventoryData = {
        blood_group: document.getElementById('invBloodGroup').value,
        rh_factor: document.getElementById('invRhFactor').value,
        quantity_ml: parseInt(document.getElementById('invQuantity').value),
        expiry_date: document.getElementById('invExpiryDate').value,
        status: document.getElementById('invStatus').value
    };

    // Validation
    if (!inventoryData.blood_group || !inventoryData.rh_factor) {
        errorEl.textContent = 'Blood group and Rh factor are required.';
        errorEl.style.display = 'block';
        return;
    }

    try {
        let result;
        if (editingInventoryId) {
            result = await apiRequest(`/inventory/${editingInventoryId}`, {
                method: 'PUT',
                body: JSON.stringify(inventoryData)
            });
        } else {
            result = await apiRequest('/inventory/', {
                method: 'POST',
                body: JSON.stringify(inventoryData)
            });
        }

        if (result && (result.status === 201 || result.status === 200)) {
            closeInventoryModal();
            loadInventory();
        } else {
            errorEl.textContent = result?.data?.detail || 'Error saving inventory.';
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