document.addEventListener('DOMContentLoaded', () => {
    const API_URL_BASE = 'http://127.0.0.1:8000/api';

    // ---- Helper: Build Table ----
    const renderTable = (containerId, data) => {
        const container = document.getElementById(containerId);
        
        if (!data || data.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="ph ph-warning-circle"></i>
                    <p>Nenhum dado encontrado para os filtros informados.</p>
                </div>
            `;
            return;
        }

        const headers = Object.keys(data[0]);
        let html = '<table class="data-table"><thead><tr>';
        
        // Headers
        headers.forEach(h => {
            html += `<th>${h}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Rows
        data.forEach(row => {
            html += '<tr>';
            headers.forEach(h => {
                html += `<td>${row[h] !== null ? row[h] : '-'}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        
        container.innerHTML = html;
    };

    // ---- Helper: Fetch Logic ----
    const fetchData = async (endpoint, btn, containerId) => {
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="ph ph-spinner ph-spin"></i> Carregando...';
        btn.disabled = true;

        const env = document.getElementById('global-env-selector').value;
        const separator = endpoint.includes('?') ? '&' : '?';
        const finalUrl = `${API_URL_BASE}${endpoint}${separator}env=${env}`;

        try {
            const response = await fetch(finalUrl);
            if (!response.ok) throw new Error('Erro na requisição da API');
            
            const data = await response.json();
            renderTable(containerId, data);
        } catch (error) {
            console.error(error);
            document.getElementById(containerId).innerHTML = `
                <div class="empty-state">
                    <i class="ph ph-x-circle text-offline"></i>
                    <p class="text-offline">Erro ao buscar dados da API. Verifique o console.</p>
                </div>
            `;
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    };

    // ---- Helper: Format Date ----
    const formatInputDate = (isoString, fallback) => {
        if (!isoString) return fallback;
        const [y, m, d] = isoString.split('-');
        return `${d}/${m}/${y}`;
    };

    // ---- Button Event Listeners ----

    // Vendas
    const btnVendas = document.getElementById('btn-vendas');
    if (btnVendas) {
        btnVendas.addEventListener('click', () => {
            const dtIniRaw = document.getElementById('vendas-dt-ini').value;
            const dtFimRaw = document.getElementById('vendas-dt-fim').value;
            
            const dtIni = formatInputDate(dtIniRaw, '01/01/2024');
            const dtFim = formatInputDate(dtFimRaw, '31/12/2024');
            
            const vendedor = document.getElementById('vendas-vendedor').value;
            
            let query = `/vendas?start_date=${encodeURIComponent(dtIni)}&end_date=${encodeURIComponent(dtFim)}`;
            if (vendedor) query += `&vendedor=${encodeURIComponent(vendedor)}`;
            
            fetchData(query, btnVendas, 'vendas-result');
        });
    }

    // Compras
    const btnCompras = document.getElementById('btn-compras');
    if (btnCompras) {
        btnCompras.addEventListener('click', () => {
            const dtIniRaw = document.getElementById('compras-dt-ini').value;
            const dtFimRaw = document.getElementById('compras-dt-fim').value;
            
            const dtIni = formatInputDate(dtIniRaw, '01/01/2024');
            const dtFim = formatInputDate(dtFimRaw, '31/12/2024');
            
            const forn = document.getElementById('compras-fornecedor').value;
            
            let query = `/compras?start_date=${encodeURIComponent(dtIni)}&end_date=${encodeURIComponent(dtFim)}`;
            if (forn) query += `&fornecedor=${encodeURIComponent(forn)}`;
            
            fetchData(query, btnCompras, 'compras-result');
        });
    }

    // Produtos
    const btnProdutos = document.getElementById('btn-produtos');
    if (btnProdutos) {
        btnProdutos.addEventListener('click', () => {
            const busca = document.getElementById('produtos-busca').value;
            let query = `/produtos`;
            if (busca) query += `?busca=${encodeURIComponent(busca)}`;
            fetchData(query, btnProdutos, 'produtos-result');
        });
    }

    // Parceiros
    const btnParceiros = document.getElementById('btn-parceiros');
    if (btnParceiros) {
        btnParceiros.addEventListener('click', () => {
            const busca = document.getElementById('parceiros-busca').value;
            const tipo = document.getElementById('parceiros-tipo').value;
            
            let query = `/parceiros?`;
            if (busca) query += `busca=${encodeURIComponent(busca)}&`;
            if (tipo) query += `tipo=${encodeURIComponent(tipo)}`;
            
            fetchData(query, btnParceiros, 'parceiros-result');
        });
    }

    // Vendedores
    const btnVendedores = document.getElementById('btn-vendedores');
    if (btnVendedores) {
        btnVendedores.addEventListener('click', () => {
            const busca = document.getElementById('vendedores-busca').value;
            let query = `/vendedores`;
            if (busca) query += `?busca=${encodeURIComponent(busca)}`;
            fetchData(query, btnVendedores, 'vendedores-result');
        });
    }


    // ---- API Status Logic ----
    const apiIndicator = document.getElementById('api-indicator');
    const apiStatusText = document.getElementById('api-status-text');
    const apiTime = document.getElementById('api-time');
    const refreshBtn = document.getElementById('refresh-btn');

    const formatTime = (date) => date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const updateStatusUI = (status) => {
        if (!apiIndicator) return;
        apiIndicator.classList.remove('loading', 'online', 'offline');
        apiStatusText.classList.remove('text-loading', 'text-online', 'text-offline');

        if (status === 'loading') {
            apiIndicator.classList.add('loading');
            apiStatusText.classList.add('text-loading');
            apiStatusText.textContent = 'Verificando...';
        } else if (status === 'online') {
            apiIndicator.classList.add('online');
            apiStatusText.classList.add('text-online');
            apiStatusText.textContent = 'Online';
        } else {
            apiIndicator.classList.add('offline');
            apiStatusText.classList.add('text-offline');
            apiStatusText.textContent = 'Offline';
        }
        if(apiTime) apiTime.textContent = formatTime(new Date());
    };

    const checkAPIStatus = async () => {
        if (!apiIndicator) return;
        if(refreshBtn) refreshBtn.disabled = true;
        updateStatusUI('loading');
        const env = document.getElementById('global-env-selector').value;
        const envText = document.getElementById('global-env-selector').options[document.getElementById('global-env-selector').selectedIndex].text;
        
        // update html elements to reflect current env
        const envDisplay = document.querySelector('.info-row .value:nth-child(2)'); // The span displaying "Sandbox" ou "Produção"
        if(envDisplay) envDisplay.innerText = envText;
        
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);
            const response = await fetch(`${API_URL_BASE}/status?env=${env}`, { method: 'GET', signal: controller.signal });
            clearTimeout(timeoutId);
            if (response.ok) updateStatusUI('online');
            else updateStatusUI('offline');
            
            // Also fetch users if we are online
            if (response.ok) fetchUsuarios();
            
        } catch (error) {
            updateStatusUI('offline');
        } finally {
            if(refreshBtn) refreshBtn.disabled = false;
        }
    };

    const fetchUsuarios = async () => {
        const tbody = document.getElementById('usuarios-tbody');
        if(!tbody) return;
        tbody.innerHTML = '<tr><td colspan="3" style="text-align: center;"><i class="ph ph-spinner ph-spin"></i> Carregando...</td></tr>';
        
        const env = document.getElementById('global-env-selector').value;
        try {
            const response = await fetch(`${API_URL_BASE}/usuarios?env=${env}`);
            if (!response.ok) throw new Error('Erro');
            const data = await response.json();
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" style="text-align: center;">Nenhum usuário encontrado.</td></tr>';
                return;
            }
            
            tbody.innerHTML = '';
            data.forEach(u => {
                const tr = document.createElement('tr');
                // Adiciona um ícone verde se logou hoje, senao cinza
                const isRecent = u.DTULTACESSO && u.DTULTACESSO.includes(new Date().toLocaleDateString('pt-BR'));
                const iconColor = isRecent ? 'var(--success)' : 'rgba(255,255,255,0.2)';
                
                tr.innerHTML = `
                    <td>${u.CODUSU}</td>
                    <td><i class="ph-fill ph-user-circle" style="color: ${iconColor}; margin-right: 8px;"></i> ${u.NOMEUSU}</td>
                    <td>${u.DTULTACESSO || '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        } catch (error) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align: center; color: var(--danger);">Falha ao carregar usuários.</td></tr>';
        }
    };

    if(refreshBtn) refreshBtn.addEventListener('click', checkAPIStatus);
    const btnRefreshUsuarios = document.getElementById('btn-refresh-usuarios');
    if (btnRefreshUsuarios) btnRefreshUsuarios.addEventListener('click', fetchUsuarios);
    
    const envSelector = document.getElementById('global-env-selector');
    if (envSelector) {
        envSelector.addEventListener('change', checkAPIStatus);
    }
    
    checkAPIStatus();

    // ---- Sidebar Navigation Logic ----
    const navItems = document.querySelectorAll('.nav-item');
    const viewSections = document.querySelectorAll('.view-section');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            viewSections.forEach(view => view.classList.remove('active'));
            
            const targetId = item.getAttribute('data-target');
            const targetView = document.getElementById(targetId);
            if (targetView) targetView.classList.add('active');
        });
    });
});
