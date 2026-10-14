window.SIDEBAR_MENU_KEYS = [
    { id: 'dashboard', icon: 'fa-chart-line', labelKey: 'sidebar.dashboard', url: '/admin/index.html' },
    { id: 'users', icon: 'fa-users', labelKey: 'sidebar.users', url: '/admin/users.html' },
    { id: 'sellers', icon: 'fa-link', labelKey: 'sidebar.sellers', url: '/admin/sellers.html' },
    { id: 'configs', icon: 'fa-bolt', labelKey: 'sidebar.configs', url: '/admin/configs.html' },
    { id: 'groups', icon: 'fa-layer-group', labelKey: 'sidebar.groups', url: '/admin/groups.html' },
    { id: 'plans', icon: 'fa-tags', labelKey: 'sidebar.plans', url: '/admin/plans.html' },
    { id: 'bot-manager', icon: 'fa-robot', labelKey: 'sidebar.bot_manager', url: '/admin/bot-manager.html' },
    { id: 'jobs', icon: 'fa-clock', labelKey: 'sidebar.jobs', url: '/admin/jobs.html' },
    { id: 'settings', icon: 'fa-cog', labelKey: 'sidebar.settings', url: '/admin/settings.html' }
];

function toggleSidebar() {
    const sidebar = document.getElementById('admin-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const lang = getCurrentLang();
    const isRtl = lang === 'fa';
    const translateHidden = isRtl ? 'translate-x-full' : '-translate-x-full';
    const translateVisible = 'translate-x-0';
    
    if (sidebar.classList.contains(translateHidden)) {
        sidebar.classList.remove(translateHidden);
        sidebar.classList.add(translateVisible);
        overlay.classList.remove('hidden');
    } else {
        sidebar.classList.remove(translateVisible);
        sidebar.classList.add(translateHidden);
        overlay.classList.add('hidden');
    }
}

function toggleLangMenu() {
    const menus = document.querySelectorAll('.lang-switcher-menu');
    menus.forEach(m => m.classList.toggle('hidden'));
}

function changeLang(lang) {
    setLang(lang);
}

function renderSidebar(activePage) {
    const lang = getCurrentLang();
    const meta = window.TRANSLATIONS[lang].meta;
    const isRtl = lang === 'fa';
    const sidePosition = isRtl ? 'right-0 border-l' : 'left-0 border-r';
    const marginSide = isRtl ? 'mr-0 md:mr-64' : 'ml-0 md:ml-64';
    const activeBorder = isRtl ? 'border-r-4' : 'border-l-4';
    const translateHidden = isRtl ? 'translate-x-full' : '-translate-x-full';
    
    const mainEl = document.querySelector('main');
    if (mainEl) {
        mainEl.classList.remove('mr-64', 'ml-64');
        mainEl.classList.add(...marginSide.split(' '), 'p-4', 'sm:p-8');
    }
    
    document.body.setAttribute('dir', meta.dir);
    document.documentElement.setAttribute('dir', meta.dir);
    document.documentElement.setAttribute('lang', lang);
    
    const brandSetting = window._brandSetting || 'NETtap';
    
    const mobileHeaderHTML = `
        <header class="md:hidden w-full bg-slate-900 border-b border-slate-800 px-4 py-3 flex items-center justify-between sticky top-0 z-30">
            <div class="flex items-center gap-3">
                <button onclick="toggleSidebar()" class="w-10 h-10 rounded-xl bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-lg text-white border border-slate-700">
                    <i class="fas fa-bars"></i>
                </button>
                <span class="text-white font-bold text-lg" data-brand>${brandSetting}</span>
            </div>
            <div class="relative">
                <button onclick="toggleLangMenu()" class="w-10 h-10 rounded-xl bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-lg border border-slate-700">
                    ${meta.flag}
                </button>
                <div class="lang-switcher-menu hidden absolute top-12 ${isRtl ? 'left-0' : 'right-0'} bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50 min-w-[150px]">
                    ${Object.keys(window.TRANSLATIONS).map(code => `
                        <button onclick="changeLang('${code}')" class="w-full px-4 py-2.5 text-sm hover:bg-slate-800 flex items-center gap-2 ${code === lang ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-300'}">
                            <span>${window.TRANSLATIONS[code].meta.flag}</span>
                            <span>${window.TRANSLATIONS[code].meta.name}</span>
                        </button>
                    `).join('')}
                </div>
            </div>
        </header>
    `;
    
    const backdropHTML = `
        <div id="sidebar-overlay" onclick="toggleSidebar()" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden transition-all duration-300"></div>
    `;
    
    const sidebarHTML = `
        <aside id="admin-sidebar" class="w-64 bg-slate-900 border-slate-800 h-screen fixed top-0 ${sidePosition} overflow-y-auto flex flex-col z-40 transition-transform duration-300 transform ${translateHidden} md:translate-x-0">
            <div class="p-6 border-b border-slate-800">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-gradient-to-tr from-indigo-600 to-violet-500 rounded-xl flex items-center justify-center text-xl shadow-lg shadow-indigo-500/20">
                        <i class="fas fa-shield-halved text-white text-lg"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-white font-bold text-lg leading-tight truncate" data-brand>${brandSetting}</div>
                        <div class="text-slate-500 text-xs">${t('common.admin_panel')}</div>
                    </div>
                </div>
            </div>
            
            <div class="p-3 border-b border-slate-800">
                <div class="relative">
                    <button onclick="toggleLangMenu()" class="w-full flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm text-slate-300 transition-all">
                        <span class="flex items-center gap-2">
                            <span class="text-base">${meta.flag}</span>
                            <span>${meta.name}</span>
                        </span>
                        <i class="fas fa-chevron-down text-xs opacity-60"></i>
                    </button>
                    <div class="lang-switcher-menu hidden absolute top-11 left-0 right-0 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">
                        ${Object.keys(window.TRANSLATIONS).map(code => `
                            <button onclick="changeLang('${code}')" class="w-full px-4 py-2.5 text-sm hover:bg-slate-800 flex items-center gap-2 ${code === lang ? 'bg-indigo-500/10 text-indigo-400' : 'text-slate-300'}">
                                <span>${window.TRANSLATIONS[code].meta.flag}</span>
                                <span class="flex-1 text-${isRtl ? 'right' : 'left'}">${window.TRANSLATIONS[code].meta.name}</span>
                                ${code === lang ? '<i class="fas fa-check text-xs"></i>' : ''}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
            
            <nav class="flex-1 p-4 space-y-1">
                ${window.SIDEBAR_MENU_KEYS.map(item => `
                    <a href="${item.url}" class="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${item.id === activePage ? `bg-indigo-600/10 text-indigo-400 ${activeBorder} border-indigo-500` : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}">
                        <i class="fas ${item.icon} w-5 text-center"></i>
                        <span>${t(item.labelKey)}</span>
                    </a>
                `).join('')}
            </nav>
            
            <div class="p-4 border-t border-slate-800">
                <button onclick="logout()" class="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-rose-400 hover:bg-rose-500/10 transition-all">
                    <i class="fas fa-right-from-bracket w-5 text-center"></i>
                    <span>${t('common.logout')}</span>
                </button>
            </div>
        </aside>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', mobileHeaderHTML);
    document.body.insertAdjacentHTML('afterbegin', backdropHTML);
    document.body.insertAdjacentHTML('afterbegin', sidebarHTML);
    
    document.addEventListener('click', (e) => {
        const menus = document.querySelectorAll('.lang-switcher-menu');
        menus.forEach(menu => {
            const parent = menu.parentElement;
            if (parent && !parent.contains(e.target)) {
                menu.classList.add('hidden');
            }
        });
    });
    
    loadBrandName();
}

async function loadBrandName() {
    try {
        const response = await fetch('/api/settings/public');
        if (response.ok) {
            const data = await response.json();
            if (data.brand_name) {
                window._brandSetting = data.brand_name;
                document.querySelectorAll('[data-brand]').forEach(el => {
                    el.textContent = data.brand_name;
                });
            }
        }
    } catch (e) {}
}