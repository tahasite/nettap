window.TRANSLATIONS = {
    en: {
        meta: { name: "English", flag: "🇬🇧", dir: "ltr", code: "en" },
        
        common: {
            save: "Save",
            cancel: "Cancel",
            delete: "Delete",
            edit: "Edit",
            add: "Add",
            close: "Close",
            back: "Back",
            next: "Next",
            yes: "Yes",
            no: "No",
            confirm: "Confirm",
            loading: "Loading...",
            search: "Search...",
            filter: "Filter",
            refresh: "Refresh",
            copy: "Copy",
            copied: "Copied!",
            export: "Export",
            import: "Import",
            all: "All",
            none: "None",
            active: "Active",
            inactive: "Inactive",
            enabled: "Enabled",
            disabled: "Disabled",
            success: "Success",
            error: "Error",
            warning: "Warning",
            info: "Info",
            total: "Total",
            status: "Status",
            actions: "Actions",
            created_at: "Created At",
            updated_at: "Updated At",
            name: "Name",
            description: "Description",
            value: "Value",
            type: "Type",
            optional: "Optional",
            required: "Required",
            select: "Select...",
            days: "days",
            hours: "hours",
            minutes: "minutes",
            seconds: "seconds",
            unlimited: "Unlimited",
            expired: "Expired",
            ready: "Ready",
            blocked: "Blocked",
            pending: "Pending",
            approved: "Approved",
            rejected: "Rejected",
            logout: "Logout",
            admin_panel: "Admin Panel"
        },
        
        sidebar: {
            dashboard: "Dashboard",
            users: "Users",
            sellers: "Seller Subs",
            configs: "Configs",
            groups: "Config Groups",
            plans: "Sales Plans",
            bot_manager: "Bot Manager",
            jobs: "Cron Jobs",
            settings: "Settings"
        },
        
        login: {
            title: "Welcome Back",
            subtitle: "Sign in to your admin panel",
            username: "Username",
            password: "Password",
            sign_in: "Sign In",
            invalid: "Invalid username or password"
        },
        
        dashboard: {
            title: "Dashboard",
            subtitle: "System overview and statistics",
            total_users: "Total Users",
            active_users: "Active Users",
            total_sellers: "Seller Subs",
            total_configs: "Configs",
            recent_users: "Recent Users",
            no_users: "No users registered yet"
        },
        
        users: {
            title: "Customer Users",
            subtitle: "Manage buyers' subscriptions",
            add_new: "Add User",
            username: "Username",
            sub_link: "Subscription Link",
            group: "Group",
            duration: "Duration",
            started: "Started",
            expires: "Expires",
            no_users: "No users found",
            waiting: "Waiting",
            default_group: "Default",
            quick_plan: "Quick Plan",
            custom_duration: "Custom Duration (minutes)",
            config_group: "Config Group (optional)",
            no_group: "No Group",
            unlimited_volume: "All subscriptions have unlimited data",
            timer_starts_on_connect: "Timer starts on first connection",
            reset_timer: "Reset timer? (Starts from next connection)",
            block_confirm: "Block user? Connection may continue for 5-15 min",
            delete_confirm: "Delete this user?",
            edit_user: "Edit User"
        },
        
        sellers: {
            title: "Seller Subscriptions",
            subtitle: "Parent subscription links from providers",
            add_new: "Add Seller Sub",
            update_all: "Update All Subs",
            sub_name: "Subscription Name",
            sub_url: "Full Subscription URL",
            last_updated: "Last Updated",
            no_sellers: "No seller subscriptions added",
            delete_confirm: "Delete this seller subscription?"
        },
        
        configs: {
            title: "System Configs",
            subtitle: "All extracted configs from seller subs",
            scan_all: "Full Scan (Country + Ping)",
            scan_countries: "Detect Countries",
            scan_ping: "Ping All",
            pin_all: "Pin All",
            unpin_all: "Unpin All",
            delete_broken: "Delete Broken",
            total: "Total Configs",
            working: "Working",
            broken: "Broken",
            pinned: "⭐ Pinned",
            countries: "🌍 Countries",
            protocol: "Protocol",
            source: "Source",
            ping: "Ping",
            all_protocols: "All Protocols",
            has_ping: "✓ Has Ping",
            no_ping: "✗ No Ping",
            fast: "⚡ Fast (<200ms)",
            medium: "🟡 Medium (200-500ms)",
            slow: "🔴 Slow (>500ms)",
            only_working: "Only Working",
            only_broken: "Only Broken",
            view: "View",
            test: "Test",
            delete_broken_confirm: "Delete all broken configs?"
        },
        
        groups: {
            title: "Config Groups",
            subtitle: "Categorize configs for specific users",
            add_new: "Create New Group",
            group_name: "Group Name",
            group_color: "Group Color",
            manage_configs: "Manage Configs",
            select_all: "All",
            select_none: "None",
            selected_count: "configs selected",
            delete_confirm: "Delete this group? Users will revert to default",
            no_groups: "No groups created yet"
        },
        
        plans: {
            title: "Sales Plans",
            subtitle: "Manage price, duration and group for each plan",
            add_new: "Add Plan",
            seed_defaults: "Default Plans",
            plan_key: "Unique Key",
            emoji: "Emoji",
            display_name: "Display Name",
            duration_minutes: "Duration (minutes)",
            price_toman: "Price (Toman)",
            free: "Free",
            is_test: "Is Test Plan?",
            display_order: "Display Order",
            is_active: "Active?",
            no_plans: "No plans created",
            use_default_or_add: "Click 'Default Plans' or add a new one"
        },
        
        settings: {
            title: "System Settings",
            subtitle: "Complete configuration and personalization",
            save_changes: "Save Changes",
            reload: "Reload",
            tips: "Note: After changing settings, click 'Save Changes'. Some changes like bot token require service restart.",
            categories: {
                general: "General",
                branding: "Branding",
                domain: "Domain & DNS",
                telegram: "Telegram Bot",
                payment: "Payment",
                subscription: "Subscription",
                advanced: "Advanced"
            }
        },
        
        bot_manager: {
            title: "Telegram Bot Manager",
            subtitle: "Configure, test and manage your bot",
            service_status: "Service Status",
            token_status: "Token Status",
            webhook_status: "Webhook Status",
            auto_setup_title: "⚡ Automatic Test & Activation",
            auto_setup_desc: "With one click, system automatically performs all steps:",
            auto_setup_btn: "Start Auto Setup",
            setup_results: "Setup Results",
            bot_info: "Bot Information",
            proxy_info: "Telegram Proxy",
            channels_check: "Force Join Channels",
            webhook_management: "Webhook Management",
            service_control: "Service Control",
            test: "Test",
            check_all: "Check All",
            set_webhook: "Set Webhook",
            delete_webhook: "Delete Webhook",
            restart_bot: "Restart Bot",
            go_to_settings: "Bot Settings",
            running: "Running",
            stopped: "Stopped",
            valid: "Valid",
            invalid: "Invalid",
            configured: "Configured",
            not_configured: "Not Configured",
            is_admin: "Admin",
            not_admin: "Not Admin"
        },
        
        jobs: {
            title: "Cron Jobs",
            subtitle: "Automatic background tasks status",
            schedule_info: "Current schedule: Scraper every 6h | IP refresh every 1h | Cleanup every 12h | Rebuild Zone every 5m",
            latest_status: "📊 Latest Status for Each Job",
            execution_history: "📜 Execution History (last 100)",
            execution_date: "Executed At",
            job_name: "Job Name",
            duration: "Duration",
            message: "Message",
            no_logs: "No logs available yet",
            last_execution: "Last Execution",
            duration_label: "Duration"
        }
    },
    
    fa: {
        meta: { name: "فارسی", flag: "🇮🇷", dir: "rtl", code: "fa" },
        
        common: {
            save: "ذخیره",
            cancel: "انصراف",
            delete: "حذف",
            edit: "ویرایش",
            add: "افزودن",
            close: "بستن",
            back: "بازگشت",
            next: "بعدی",
            yes: "بله",
            no: "خیر",
            confirm: "تایید",
            loading: "در حال بارگذاری...",
            search: "جستجو...",
            filter: "فیلتر",
            refresh: "بروزرسانی",
            copy: "کپی",
            copied: "کپی شد!",
            export: "خروجی",
            import: "ورودی",
            all: "همه",
            none: "هیچ",
            active: "فعال",
            inactive: "غیرفعال",
            enabled: "فعال",
            disabled: "غیرفعال",
            success: "موفق",
            error: "خطا",
            warning: "هشدار",
            info: "اطلاع",
            total: "کل",
            status: "وضعیت",
            actions: "عملیات",
            created_at: "تاریخ ایجاد",
            updated_at: "آخرین بروزرسانی",
            name: "نام",
            description: "توضیحات",
            value: "مقدار",
            type: "نوع",
            optional: "اختیاری",
            required: "اجباری",
            select: "انتخاب کنید...",
            days: "روز",
            hours: "ساعت",
            minutes: "دقیقه",
            seconds: "ثانیه",
            unlimited: "نامحدود",
            expired: "منقضی",
            ready: "آماده",
            blocked: "مسدود",
            pending: "در انتظار",
            approved: "تایید شده",
            rejected: "رد شده",
            logout: "خروج",
            admin_panel: "پنل مدیریت"
        },
        
        sidebar: {
            dashboard: "داشبورد",
            users: "کاربران",
            sellers: "ساب‌های فروشنده",
            configs: "کانفیگ‌ها",
            groups: "گروه‌های کانفیگ",
            plans: "پلن‌های فروش",
            bot_manager: "مدیریت ربات",
            jobs: "کرون‌جاب‌ها",
            settings: "تنظیمات"
        },
        
        login: {
            title: "خوش آمدید",
            subtitle: "به پنل مدیریت وارد شوید",
            username: "نام کاربری",
            password: "رمز عبور",
            sign_in: "ورود",
            invalid: "نام کاربری یا رمز عبور اشتباه است"
        },
        
        dashboard: {
            title: "داشبورد",
            subtitle: "نمای کلی سیستم و آمار",
            total_users: "کل کاربران",
            active_users: "کاربران فعال",
            total_sellers: "ساب فروشندگان",
            total_configs: "کانفیگ‌ها",
            recent_users: "آخرین کاربران",
            no_users: "هنوز کاربری ثبت نشده"
        },
        
        users: {
            title: "کاربران خریدار",
            subtitle: "مدیریت اشتراک خریداران",
            add_new: "افزودن کاربر",
            username: "نام کاربری",
            sub_link: "لینک اشتراک",
            group: "گروه",
            duration: "مدت",
            started: "شروع",
            expires: "انقضا",
            no_users: "کاربری یافت نشد",
            waiting: "در انتظار",
            default_group: "پیش‌فرض",
            quick_plan: "پلن سریع",
            custom_duration: "مدت دلخواه (دقیقه)",
            config_group: "گروه کانفیگ (اختیاری)",
            no_group: "بدون گروه",
            unlimited_volume: "همه اشتراک‌ها حجم نامحدود هستند",
            timer_starts_on_connect: "زمان از اولین اتصال شروع می‌شود",
            reset_timer: "تایمر ریست شود؟ (از اتصال بعدی شروع می‌شود)",
            block_confirm: "مسدود شود؟ تا 5-15 دقیقه اتصال زنده ادامه دارد",
            delete_confirm: "این کاربر حذف شود؟",
            edit_user: "ویرایش کاربر"
        },
        
        sellers: {
            title: "ساب‌های فروشنده",
            subtitle: "لینک‌های مادر از فروشندگان",
            add_new: "افزودن ساب فروشنده",
            update_all: "بروزرسانی همه ساب‌ها",
            sub_name: "نام ساب",
            sub_url: "آدرس کامل اشتراک",
            last_updated: "آخرین بروزرسانی",
            no_sellers: "هیچ ساب فروشنده‌ای ثبت نشده",
            delete_confirm: "این ساب فروشنده حذف شود؟"
        },
        
        configs: {
            title: "کانفیگ‌های سیستم",
            subtitle: "تمام کانفیگ‌های استخراج‌شده از ساب‌ها",
            scan_all: "اسکن کامل (کشور + پینگ)",
            scan_countries: "تشخیص کشور",
            scan_ping: "تست پینگ",
            pin_all: "ستاره‌دار کردن همه",
            unpin_all: "حذف ستاره همه",
            delete_broken: "حذف خراب‌ها",
            total: "کل کانفیگ‌ها",
            working: "سالم",
            broken: "خراب",
            pinned: "⭐ ستاره‌دار",
            countries: "🌍 کشورها",
            protocol: "پروتکل",
            source: "منبع",
            ping: "پینگ",
            all_protocols: "همه پروتکل‌ها",
            has_ping: "✓ پینگ دارد",
            no_ping: "✗ پینگ ندارد",
            fast: "⚡ سریع (<200ms)",
            medium: "🟡 متوسط (200-500ms)",
            slow: "🔴 کند (>500ms)",
            only_working: "فقط سالم",
            only_broken: "فقط خراب",
            view: "مشاهده",
            test: "تست",
            delete_broken_confirm: "همه کانفیگ‌های خراب حذف شوند؟"
        },
        
        groups: {
            title: "گروه‌های کانفیگ",
            subtitle: "دسته‌بندی کانفیگ‌ها برای کاربران خاص",
            add_new: "ساخت گروه جدید",
            group_name: "نام گروه",
            group_color: "رنگ گروه",
            manage_configs: "مدیریت کانفیگ‌ها",
            select_all: "همه",
            select_none: "هیچ",
            selected_count: "کانفیگ انتخاب شده",
            delete_confirm: "این گروه حذف شود؟ کاربران به حالت پیش‌فرض برمی‌گردند",
            no_groups: "هیچ گروهی ساخته نشده"
        },
        
        plans: {
            title: "پلن‌های فروش",
            subtitle: "مدیریت قیمت، مدت و گروه هر پلن",
            add_new: "افزودن پلن",
            seed_defaults: "پلن‌های پیش‌فرض",
            plan_key: "کلید یکتا",
            emoji: "ایموجی",
            display_name: "نام نمایشی",
            duration_minutes: "مدت (دقیقه)",
            price_toman: "قیمت (تومان)",
            free: "رایگان",
            is_test: "پلن تست؟",
            display_order: "ترتیب نمایش",
            is_active: "فعال؟",
            no_plans: "هیچ پلنی ثبت نشده",
            use_default_or_add: "دکمه «پلن‌های پیش‌فرض» را بزنید یا پلن جدید اضافه کنید"
        },
        
        settings: {
            title: "تنظیمات سیستم",
            subtitle: "پیکربندی و شخصی‌سازی کامل",
            save_changes: "ذخیره تغییرات",
            reload: "بروزرسانی",
            tips: "نکته: پس از تغییر تنظیمات، روی «ذخیره تغییرات» کلیک کنید. برخی تغییرات نیاز به ری‌استارت سرویس دارند.",
            categories: {
                general: "عمومی",
                branding: "برندینگ",
                domain: "دامنه و DNS",
                telegram: "ربات تلگرام",
                payment: "پرداخت",
                subscription: "اشتراک",
                advanced: "پیشرفته"
            }
        },
        
        bot_manager: {
            title: "مدیریت ربات تلگرام",
            subtitle: "تنظیم، تست و مدیریت کامل ربات",
            service_status: "وضعیت سرویس",
            token_status: "وضعیت توکن",
            webhook_status: "وضعیت Webhook",
            auto_setup_title: "⚡ تست و فعال‌سازی خودکار",
            auto_setup_desc: "با یک کلیک، سیستم تمام مراحل زیر را خودکار انجام می‌دهد:",
            auto_setup_btn: "شروع فعال‌سازی خودکار",
            setup_results: "نتایج فعال‌سازی",
            bot_info: "اطلاعات ربات",
            proxy_info: "پروکسی تلگرام",
            channels_check: "کانال‌های عضویت اجباری",
            webhook_management: "مدیریت Webhook",
            service_control: "کنترل سرویس",
            test: "تست",
            check_all: "بررسی همه",
            set_webhook: "تنظیم Webhook",
            delete_webhook: "حذف Webhook",
            restart_bot: "ری‌استارت ربات",
            go_to_settings: "تنظیمات ربات",
            running: "فعال",
            stopped: "متوقف",
            valid: "معتبر",
            invalid: "نامعتبر",
            configured: "تنظیم شده",
            not_configured: "تنظیم نشده",
            is_admin: "ادمین",
            not_admin: "ادمین نیست"
        },
        
        jobs: {
            title: "کرون‌جاب‌ها",
            subtitle: "وضعیت تسک‌های خودکار پس‌زمینه",
            schedule_info: "زمان‌بندی فعلی: Scraper هر 6 ساعت | بروزرسانی IP هر 1 ساعت | پاک‌سازی هر 12 ساعت | Rebuild Zone هر 5 دقیقه",
            latest_status: "📊 آخرین وضعیت هر کار",
            execution_history: "📜 تاریخچه اجرا (100 مورد آخر)",
            execution_date: "تاریخ اجرا",
            job_name: "نام کار",
            duration: "مدت",
            message: "پیام",
            no_logs: "هنوز لاگی موجود نیست",
            last_execution: "آخرین اجرا",
            duration_label: "مدت زمان"
        }
    },
    
    ru: {
        meta: { name: "Русский", flag: "🇷🇺", dir: "ltr", code: "ru" },
        
        common: {
            save: "Сохранить",
            cancel: "Отмена",
            delete: "Удалить",
            edit: "Изменить",
            add: "Добавить",
            close: "Закрыть",
            back: "Назад",
            next: "Далее",
            yes: "Да",
            no: "Нет",
            confirm: "Подтвердить",
            loading: "Загрузка...",
            search: "Поиск...",
            filter: "Фильтр",
            refresh: "Обновить",
            copy: "Копировать",
            copied: "Скопировано!",
            export: "Экспорт",
            import: "Импорт",
            all: "Все",
            none: "Ничего",
            active: "Активен",
            inactive: "Неактивен",
            enabled: "Включено",
            disabled: "Отключено",
            success: "Успешно",
            error: "Ошибка",
            warning: "Внимание",
            info: "Информация",
            total: "Всего",
            status: "Статус",
            actions: "Действия",
            created_at: "Создано",
            updated_at: "Обновлено",
            name: "Имя",
            description: "Описание",
            value: "Значение",
            type: "Тип",
            optional: "Опционально",
            required: "Обязательно",
            select: "Выбрать...",
            days: "дней",
            hours: "часов",
            minutes: "минут",
            seconds: "секунд",
            unlimited: "Безлимитно",
            expired: "Истёк",
            ready: "Готов",
            blocked: "Заблокирован",
            pending: "В ожидании",
            approved: "Одобрено",
            rejected: "Отклонено",
            logout: "Выход",
            admin_panel: "Админ-панель"
        },
        
        sidebar: {
            dashboard: "Панель",
            users: "Пользователи",
            sellers: "Подписки продавцов",
            configs: "Конфиги",
            groups: "Группы конфигов",
            plans: "Планы продаж",
            bot_manager: "Менеджер бота",
            jobs: "Задания",
            settings: "Настройки"
        },
        
        login: {
            title: "С возвращением",
            subtitle: "Войдите в админ-панель",
            username: "Имя пользователя",
            password: "Пароль",
            sign_in: "Войти",
            invalid: "Неверное имя пользователя или пароль"
        },
        
        dashboard: {
            title: "Панель управления",
            subtitle: "Обзор системы и статистика",
            total_users: "Всего пользователей",
            active_users: "Активные",
            total_sellers: "Подписок продавцов",
            total_configs: "Конфигов",
            recent_users: "Последние пользователи",
            no_users: "Нет зарегистрированных пользователей"
        },
        
        users: {
            title: "Пользователи",
            subtitle: "Управление подписками покупателей",
            add_new: "Добавить пользователя",
            username: "Имя пользователя",
            sub_link: "Ссылка подписки",
            group: "Группа",
            duration: "Длительность",
            started: "Начало",
            expires: "Истекает",
            no_users: "Пользователи не найдены",
            waiting: "Ожидание",
            default_group: "По умолчанию",
            quick_plan: "Быстрый план",
            custom_duration: "Своё время (минуты)",
            config_group: "Группа конфигов (опционально)",
            no_group: "Без группы",
            unlimited_volume: "Все подписки безлимитные по трафику",
            timer_starts_on_connect: "Таймер начинается при первом подключении",
            reset_timer: "Сбросить таймер? (Начнётся при следующем подключении)",
            block_confirm: "Заблокировать? Активные соединения продолжатся 5-15 мин",
            delete_confirm: "Удалить этого пользователя?",
            edit_user: "Изменить пользователя"
        },
        
        sellers: {
            title: "Подписки продавцов",
            subtitle: "Основные ссылки от провайдеров",
            add_new: "Добавить подписку",
            update_all: "Обновить все",
            sub_name: "Название",
            sub_url: "Полный URL подписки",
            last_updated: "Последнее обновление",
            no_sellers: "Нет добавленных подписок",
            delete_confirm: "Удалить эту подписку?"
        },
        
        configs: {
            title: "Конфиги системы",
            subtitle: "Все извлечённые конфиги",
            scan_all: "Полное сканирование",
            scan_countries: "Определить страны",
            scan_ping: "Проверить пинг",
            pin_all: "Закрепить все",
            unpin_all: "Открепить все",
            delete_broken: "Удалить сломанные",
            total: "Всего",
            working: "Рабочие",
            broken: "Сломанные",
            pinned: "⭐ Закреплённые",
            countries: "🌍 Страны",
            protocol: "Протокол",
            source: "Источник",
            ping: "Пинг",
            all_protocols: "Все протоколы",
            has_ping: "✓ Есть пинг",
            no_ping: "✗ Нет пинга",
            fast: "⚡ Быстрый (<200мс)",
            medium: "🟡 Средний (200-500мс)",
            slow: "🔴 Медленный (>500мс)",
            only_working: "Только рабочие",
            only_broken: "Только сломанные",
            view: "Просмотр",
            test: "Тест",
            delete_broken_confirm: "Удалить все сломанные конфиги?"
        },
        
        groups: {
            title: "Группы конфигов",
            subtitle: "Категоризация конфигов для пользователей",
            add_new: "Создать группу",
            group_name: "Имя группы",
            group_color: "Цвет группы",
            manage_configs: "Управление конфигами",
            select_all: "Все",
            select_none: "Ничего",
            selected_count: "конфигов выбрано",
            delete_confirm: "Удалить группу? Пользователи вернутся к по умолчанию",
            no_groups: "Группы не созданы"
        },
        
        plans: {
            title: "Планы продаж",
            subtitle: "Управление ценой, длительностью и группой",
            add_new: "Добавить план",
            seed_defaults: "Планы по умолчанию",
            plan_key: "Уникальный ключ",
            emoji: "Эмодзи",
            display_name: "Отображаемое имя",
            duration_minutes: "Длительность (минуты)",
            price_toman: "Цена (Томан)",
            free: "Бесплатно",
            is_test: "Тестовый план?",
            display_order: "Порядок",
            is_active: "Активен?",
            no_plans: "Нет планов",
            use_default_or_add: "Нажмите 'Планы по умолчанию' или добавьте новый"
        },
        
        settings: {
            title: "Настройки системы",
            subtitle: "Полная настройка и персонализация",
            save_changes: "Сохранить",
            reload: "Обновить",
            tips: "Внимание: После изменения настроек нажмите 'Сохранить'. Некоторые изменения требуют перезапуска сервиса.",
            categories: {
                general: "Общие",
                branding: "Брендинг",
                domain: "Домен и DNS",
                telegram: "Telegram бот",
                payment: "Оплата",
                subscription: "Подписка",
                advanced: "Расширенные"
            }
        },
        
        bot_manager: {
            title: "Менеджер Telegram бота",
            subtitle: "Настройка, тест и управление",
            service_status: "Статус сервиса",
            token_status: "Статус токена",
            webhook_status: "Статус Webhook",
            auto_setup_title: "⚡ Авто-настройка",
            auto_setup_desc: "Одним кликом система выполнит все шаги:",
            auto_setup_btn: "Начать авто-настройку",
            setup_results: "Результаты настройки",
            bot_info: "Информация о боте",
            proxy_info: "Telegram прокси",
            channels_check: "Обязательные каналы",
            webhook_management: "Управление Webhook",
            service_control: "Управление сервисом",
            test: "Тест",
            check_all: "Проверить все",
            set_webhook: "Установить Webhook",
            delete_webhook: "Удалить Webhook",
            restart_bot: "Перезапустить бота",
            go_to_settings: "Настройки бота",
            running: "Работает",
            stopped: "Остановлен",
            valid: "Действителен",
            invalid: "Недействителен",
            configured: "Настроен",
            not_configured: "Не настроен",
            is_admin: "Админ",
            not_admin: "Не админ"
        },
        
        jobs: {
            title: "Cron Jobs",
            subtitle: "Статус автоматических фоновых задач",
            schedule_info: "Расписание: Scraper каждые 6ч | IP каждые 1ч | Очистка каждые 12ч | Rebuild Zone каждые 5м",
            latest_status: "📊 Последний статус каждого задания",
            execution_history: "📜 История выполнения (последние 100)",
            execution_date: "Дата выполнения",
            job_name: "Имя задания",
            duration: "Длительность",
            message: "Сообщение",
            no_logs: "Логов пока нет",
            last_execution: "Последнее выполнение",
            duration_label: "Длительность"
        }
    }
};

function getCurrentLang() {
    const saved = localStorage.getItem('admin_lang');
    if (saved && window.TRANSLATIONS[saved]) return saved;
    const browserLang = (navigator.language || 'en').substring(0, 2);
    if (window.TRANSLATIONS[browserLang]) return browserLang;
    return 'en';
}

function setLang(lang) {
    if (!window.TRANSLATIONS[lang]) return;
    localStorage.setItem('admin_lang', lang);
    location.reload();
}

function t(path, fallback = '') {
    const lang = getCurrentLang();
    const translations = window.TRANSLATIONS[lang] || window.TRANSLATIONS.en;
    const keys = path.split('.');
    let result = translations;
    for (const key of keys) {
        if (result && typeof result === 'object' && key in result) {
            result = result[key];
        } else {
            const enFallback = window.TRANSLATIONS.en;
            let enResult = enFallback;
            for (const k of keys) {
                if (enResult && typeof enResult === 'object' && k in enResult) {
                    enResult = enResult[k];
                } else {
                    return fallback || path;
                }
            }
            return enResult || fallback || path;
        }
    }
    return result;
}

function applyLangToDocument() {
    const lang = getCurrentLang();
    const meta = window.TRANSLATIONS[lang].meta;
    document.documentElement.setAttribute('lang', lang);
    document.documentElement.setAttribute('dir', meta.dir);
    
    document.querySelectorAll('[data-t]').forEach(el => {
        const key = el.getAttribute('data-t');
        const value = t(key);
        if (value) el.textContent = value;
    });
    
    document.querySelectorAll('[data-t-placeholder]').forEach(el => {
        const key = el.getAttribute('data-t-placeholder');
        const value = t(key);
        if (value) el.setAttribute('placeholder', value);
    });
    
    document.querySelectorAll('[data-t-title]').forEach(el => {
        const key = el.getAttribute('data-t-title');
        const value = t(key);
        if (value) el.setAttribute('title', value);
    });
}

window.getCurrentLang = getCurrentLang;
window.setLang = setLang;
window.t = t;
window.applyLangToDocument = applyLangToDocument;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyLangToDocument);
} else {
    applyLangToDocument();
}