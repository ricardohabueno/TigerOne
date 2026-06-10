const API_BASE_URL = '/api';

document.addEventListener('DOMContentLoaded', () => {
    loadCampaigns();
    setupModal();
});

let allCampaigns = [];

async function loadCampaigns() {
    try {
        const response = await fetch(`${API_BASE_URL}/campaigns`);
        allCampaigns = await response.json();
        renderCampaigns(allCampaigns);
    } catch (error) {
        console.error("Erro ao carregar campanhas:", error);
    }
}

function renderCampaigns(campaigns) {
    const container = document.getElementById('campaignGroups');
    container.innerHTML = '';

    const categories = ['Relacionamento', 'Recuperação', 'Marketing'];
    
    categories.forEach(category => {
        const categoryCampaigns = campaigns.filter(c => c.category === category);
        
        if (categoryCampaigns.length === 0) return;

        const section = document.createElement('div');
        section.className = 'group-section';
        
        const header = document.createElement('div');
        header.className = `group-header ${category.toLowerCase().replace('ç', 'c').replace('ã', 'a')}`;
        header.textContent = category;
        section.appendChild(header);

        categoryCampaigns.forEach(campaign => {
            const row = document.createElement('div');
            row.className = 'row';
            
            const isChecked = campaign.is_active ? 'checked' : '';
            const lastSent = campaign.last_sent ? new Date(campaign.last_sent).toLocaleString('pt-BR') : 'Nunca enviado';
            const nextSent = campaign.next_sent ? new Date(campaign.next_sent).toLocaleString('pt-BR') : 'Aguardando ativação';

            const extraFieldsHtml = campaign.include_schedule_fields ? `
                <div style="display: flex; gap: 5px; margin-top: 4px;">
                    <input type="text" id="testDate_${campaign.id}" placeholder="Data (Ex: 26/05/2026)" value="${campaign.test_date || ''}" onblur="saveTestData(${campaign.id})" oninput="this.value = this.value.replace(/[^0-9]/g, '').replace(/^([0-9]{2})([0-9]{1,2})?([0-9]{1,4})?/, function(m, p1, p2, p3) { return p1 + (p2 ? '/' + p2 : '') + (p3 ? '/' + p3 : ''); }).slice(0,10);" style="flex:1; padding: 4px; font-size: 11px; border: 1px solid #ddd; border-radius: 4px;">
                    <input type="text" id="testTime_${campaign.id}" placeholder="Hora (Ex: 10:30)" value="${campaign.test_time || ''}" onblur="saveTestData(${campaign.id})" oninput="this.value = this.value.replace(/[^0-9]/g, '').replace(/^([0-9]{2})([0-9]{1,2})?/, function(m, p1, p2) { return p1 + (p2 ? ':' + p2 : ''); }).slice(0,5);" style="flex:1; padding: 4px; font-size: 11px; border: 1px solid #ddd; border-radius: 4px;">
                </div>
            ` : '';

            const conversionStatsHtml = campaign.track_conversions ? `
                <div class="conversion-stats">
                    <strong>Envios:</strong> ${campaign.sent_count} | 
                    <strong>Retornos:</strong> ${campaign.converted_count} 
                    <span style="color: #ff4d4f; font-weight: bold; margin-left: 2px; margin-right: 2px;">(${campaign.conversion_rate}%)</span> | 
                    <strong>Faturamento Est.:</strong> R$ ${campaign.revenue_recovered.toLocaleString('pt-BR', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </div>
            ` : '';

            row.innerHTML = `
                <div class="col-toggle">
                    <label class="switch">
                        <input type="checkbox" ${isChecked} onchange="toggleCampaign(${campaign.id}, this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="col-name" style="display: flex; flex-direction: column; gap: 5px;">
                    <strong>${campaign.name}</strong>
                    <div style="display: flex; gap: 5px;">
                        <input type="text" id="testName_${campaign.id}" placeholder="Nome Teste" value="${campaign.test_name || ''}" onblur="saveTestData(${campaign.id})" style="flex:1; padding: 4px; font-size: 11px; border: 1px solid #ddd; border-radius: 4px;">
                        <input type="text" id="testPhone_${campaign.id}" placeholder="Tel (55119...)" value="${campaign.test_phone || ''}" onblur="saveTestData(${campaign.id})" style="flex:1; padding: 4px; font-size: 11px; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                    ${extraFieldsHtml}
                    ${conversionStatsHtml}
                </div>
                <div class="col-date">${lastSent}</div>
                <div class="col-date">${nextSent}</div>
                <div class="col-actions">
                    <button class="btn btn-test" onclick="sendTest(${campaign.id})">TESTAR</button>
                    <button class="btn btn-log" onclick="showLog(${campaign.id}, '${campaign.name}')">LOG</button>
                    <button class="btn btn-config" onclick="openConfig(${campaign.id})">CONFIGURAÇÕES</button>
                </div>
            `;
            section.appendChild(row);
        });

        container.appendChild(section);
    });
}

async function toggleCampaign(id, isActive) {
    try {
        await fetch(`${API_BASE_URL}/campaigns/${id}/toggle`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });
    } catch (error) {
        console.error("Erro ao alterar status da campanha:", error);
        alert("Falha ao salvar. Tente novamente.");
    }
}

function formatTime(val) {
    if (!val) return '';
    // If it contains a letter like 'h' or 'H', normalize to colon
    val = val.replace(/[hH]/g, ':').replace(/[^0-9:]/g, '');
    if (val.includes(':')) {
        let parts = val.split(':');
        let hh = parts[0].replace(/[^0-9]/g, '');
        let mm = parts[1].replace(/[^0-9]/g, '') || '00';
        if (hh.length === 1) hh = '0' + hh;
        if (mm.length === 1) mm = mm + '0';
        let hhInt = parseInt(hh, 10) || 0;
        let mmInt = parseInt(mm, 10) || 0;
        if (hhInt >= 24) hhInt = hhInt % 24;
        if (mmInt >= 60) mmInt = mmInt % 60;
        return String(hhInt).padStart(2, '0') + ':' + String(mmInt).padStart(2, '0');
    }
    val = val.replace(/[^0-9]/g, '');
    if (val.length === 1) val = '0' + val + '00';
    else if (val.length === 2) val = val + '00';
    else if (val.length === 3) val = '0' + val;
    if (val.length >= 4) {
        let hh = val.substring(0, 2);
        let mm = val.substring(2, 4);
        let hhInt = parseInt(hh, 10) || 0;
        let mmInt = parseInt(mm, 10) || 0;
        if (hhInt >= 24) hhInt = hhInt % 24;
        if (mmInt >= 60) mmInt = mmInt % 60;
        return String(hhInt).padStart(2, '0') + ':' + String(mmInt).padStart(2, '0');
    }
    return val;
}

function formatDate(val) {
    if (!val) return '';
    // If it contains slash or dash, split
    let cleaned = val.replace(/[^0-9/\-]/g, '').replace(/-/g, '/');
    if (cleaned.includes('/')) {
        let parts = cleaned.split('/');
        let dd = parts[0].replace(/[^0-9]/g, '');
        let mm = parts[1] ? parts[1].replace(/[^0-9]/g, '') : '';
        let yyyy = parts[2] ? parts[2].replace(/[^0-9]/g, '') : '';
        const now = new Date();
        if (!dd) dd = String(now.getDate()).padStart(2, '0');
        if (!mm) mm = String(now.getMonth() + 1).padStart(2, '0');
        if (!yyyy) yyyy = String(now.getFullYear());
        if (dd.length === 1) dd = '0' + dd;
        if (mm.length === 1) mm = '0' + mm;
        if (yyyy.length === 2) yyyy = '20' + yyyy;
        return dd + '/' + mm + '/' + yyyy;
    }
    let valDigits = val.replace(/[^0-9]/g, '');
    if (valDigits.length === 2) {
        const now = new Date();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const y = now.getFullYear();
        return valDigits + '/' + m + '/' + y;
    }
    if (valDigits.length === 4) {
        const now = new Date();
        const y = now.getFullYear();
        return valDigits.substring(0, 2) + '/' + valDigits.substring(2, 4) + '/' + y;
    }
    if (valDigits.length === 6) {
        return valDigits.substring(0, 2) + '/' + valDigits.substring(2, 4) + '/20' + valDigits.substring(4, 6);
    }
    if (valDigits.length === 8) {
        return valDigits.substring(0, 2) + '/' + valDigits.substring(2, 4) + '/' + valDigits.substring(4, 8);
    }
    return val;
}

async function saveTestData(id) {
    const campaign = allCampaigns.find(c => c.id === id);
    if (!campaign) return;

    const testName = document.getElementById(`testName_${id}`).value;
    const testPhone = document.getElementById(`testPhone_${id}`).value;
    
    const payload = {
        test_name: testName,
        test_phone: testPhone
    };

    if (campaign.include_schedule_fields) {
        const dateInput = document.getElementById(`testDate_${id}`);
        const timeInput = document.getElementById(`testTime_${id}`);
        
        dateInput.value = formatDate(dateInput.value);
        timeInput.value = formatTime(timeInput.value);
        
        payload.test_date = dateInput.value;
        payload.test_time = timeInput.value;
    }

    try {
        await fetch(`${API_BASE_URL}/campaigns/${id}/test-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    } catch (error) {
        console.error("Erro ao salvar dados de teste:", error);
    }
}

async function sendTest(id) {
    const campaign = allCampaigns.find(c => c.id === id);
    if (!campaign) return;

    const testName = document.getElementById(`testName_${id}`).value;
    const testPhone = document.getElementById(`testPhone_${id}`).value;

    if (!testName || !testPhone) {
        alert("Por favor, preencha Nome Teste e Tel Teste antes de testar.");
        return;
    }

    const payload = {
        nome: testName,
        telefone: testPhone
    };

    if (campaign.include_schedule_fields) {
        const dateInput = document.getElementById(`testDate_${id}`);
        const timeInput = document.getElementById(`testTime_${id}`);
        
        dateInput.value = formatDate(dateInput.value);
        timeInput.value = formatTime(timeInput.value);
        
        payload.avecreserva = dateInput.value;
        payload.avechorario = timeInput.value;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/campaigns/${id}/test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (response.ok) {
            alert("Disparo de teste enviado com sucesso!");
        } else {
            alert("Erro no teste: " + (data.detail || JSON.stringify(data)));
        }
    } catch (error) {
        console.error("Erro ao disparar teste:", error);
        alert("Erro de conexão ao disparar teste.");
    }
}

async function fetchData() {
    try {
        const response = await fetch(`${API_BASE_URL}/fetch-data`, { method: 'POST' });
        if (response.ok) {
            alert('A extração dos dados (Simulação) foi iniciada. Acompanhe os resultados no LOG em alguns segundos.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao iniciar extração.');
    }
}

async function refreshConversions() {
    try {
        const response = await fetch(`${API_BASE_URL}/conversions/refresh`, { method: 'POST' });
        if (response.ok) {
            alert('A atualização de conversões foi iniciada. As estatísticas e logs serão atualizados em alguns segundos.');
            setTimeout(loadCampaigns, 4000);
        }
    } catch (error) {
        console.error('Erro ao atualizar conversões:', error);
        alert('Erro ao atualizar conversões.');
    }
}

async function triggerAll() {
    if(!confirm("Atenção: Isso vai ignorar os horários agendados e disparar mensagens REAIS de WhatsApp agora mesmo! Tem certeza?")) {
        return;
    }
    try {
        const response = await fetch(`${API_BASE_URL}/trigger-all`, { method: 'POST' });
        if (response.ok) {
            alert('DISPARO REAL iniciado em background! Verifique os logs.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao disparar campanhas.');
    }
}

function setupModal() {
    const modal = document.getElementById('settingsModal');
    const btn = document.getElementById('globalSettingsBtn');
    const span = document.getElementsByClassName('close')[0];
    const form = document.getElementById('settingsForm');

    btn.onclick = async () => {
        // Fetch current settings
        try {
            const response = await fetch(`${API_BASE_URL}/settings`);
            const settings = await response.json();
            document.getElementById('avecUsername').value = settings.avec_username || '';
            document.getElementById('avecPassword').value = settings.avec_password || '';
            document.getElementById('avecSalonId').value = settings.avec_salon_id || '';
        } catch (error) {
            console.error("Erro ao carregar configs:", error);
        }
        modal.classList.add('show');
    }

    span.onclick = () => modal.classList.remove('show');
    window.onclick = (event) => {
        if (event.target == modal) {
            modal.classList.remove('show');
        }
    }

    form.onsubmit = async (e) => {
        e.preventDefault();
        const data = {
            avec_username: document.getElementById('avecUsername').value,
            avec_password: document.getElementById('avecPassword').value,
            avec_salon_id: document.getElementById('avecSalonId').value
        };

        try {
            await fetch(`${API_BASE_URL}/settings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            modal.classList.remove('show');
            alert('Configurações salvas com sucesso!');
        } catch (error) {
            console.error("Erro ao salvar configs:", error);
            alert('Falha ao salvar configurações.');
        }
    }
}

function openConfig(id) {
    const campaign = allCampaigns.find(c => c.id === id);
    if (!campaign) return;

    document.getElementById('configCampaignId').value = id;
    document.getElementById('wizebotUrl').value = campaign.wizebot_webhook_url || '';
    document.getElementById('avecReportUrl').value = campaign.avec_report_url || '';
    
    let ruleText = "";
    if (campaign.extraction_offset_days === 0) ruleText = "Hoje";
    else if (campaign.extraction_offset_days === 1) ruleText = "Amanhã (+1 dia)";
    else if (campaign.extraction_offset_days === 7) ruleText = "Daqui a 7 dias (+7 dias)";
    else if (campaign.extraction_offset_days === -1) ruleText = "Ontem (-1 dia)";
    else if (campaign.extraction_offset_days < 0) ruleText = `Há ${Math.abs(campaign.extraction_offset_days)} dias atrás (${campaign.extraction_offset_days} dias)`;
    else ruleText = `Daqui a ${campaign.extraction_offset_days} dias (+${campaign.extraction_offset_days} dias)`;
    
    document.getElementById('configRuleText').textContent = ruleText;
    
    const modal = document.getElementById('configModal');
    modal.style.display = 'block';
}

function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
}

async function showLog(campaignId, campaignName) {
    try {
        const response = await fetch(`${API_BASE_URL}/campaigns/${campaignId}/logs`);
        const data = await response.json();
        
        document.getElementById('logModalTitle').textContent = `Logs: ${campaignName}`;
        document.getElementById('logContent').textContent = data.log || "Nenhum log disponível.";
        document.getElementById('logModal').style.display = 'block';
    } catch (e) {
        alert("Erro ao buscar logs: " + e);
    }
}

function closeLogModal() {
    document.getElementById('logModal').style.display = 'none';
}

// Setup Event Listeners para o Modal da Campanha
document.addEventListener('DOMContentLoaded', () => {
    const formConfig = document.getElementById('configForm');

    formConfig.onsubmit = async (e) => {
        e.preventDefault();
        const id = document.getElementById('configCampaignId').value;
        const data = {
            wizebot_webhook_url: document.getElementById('wizebotUrl').value,
            avec_report_url: document.getElementById('avecReportUrl').value
        };

        try {
            await fetch(`${API_BASE_URL}/campaigns/${id}/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            closeConfigModal();
            alert('Configurações da campanha salvas com sucesso!');
            loadCampaigns(); // Atualiza localmente
        } catch (error) {
            console.error("Erro ao salvar configs da campanha:", error);
            alert('Falha ao salvar configurações.');
        }
    }
});
