(function () {
    var THEME_KEY = "cryptotrade-theme";
    var USERS_KEY = "cryptotrade-users";
    var SESSION_KEY = "cryptotrade-session";
    var DATA_KEY = "cryptotrade-data";
    var PRICE_SYNC_KEY = "cryptotrade-price-sync";
    var API_STATE_URL = "/api/state";
    var DARK_THEME = "dark";
    var LIGHT_THEME = "light";
    var PRICE_MODE_AUTO = "auto";
    var PRICE_MODE_MANUAL = "manual";
    var PRICE_SOURCE_BINANCE = "binance";
    var BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr";
    var PRICE_SYNC_INTERVAL_MS = 30000;
    var CHART_REFRESH_INTERVAL_MS = 30000;
    var MARKET_CANDLE_LIMIT = 240;
    var MARKET_CANDLE_CACHE_MS = 30000;
    var SIMULATION_RESUME_GRACE_MS = 15000;
    var SIMULATION_TICK_INTERVAL_MS = 5000;
    var SIMULATION_PREFIX = "sim-";
    var SIMULATION_HISTORY_LIMIT = 400;
    var ROLE_TRADER = "trader";
    var ROLE_ADMIN = "admin";
    var ROLE_SIMULATOR = "simulator";
    var START_BALANCE = 10000;
    var DEMO_CREATED_AT = "2026-06-08T00:00:00.000Z";
    var databaseStateCache = null;
    var databaseAvailable = false;
    var marketCandleCache = {};
    var SIMULATION_NAMES = ["Антон Миронов", "Елена Волкова", "Игорь Соколов", "Мария Орлова", "Дмитрий Котов", "Ольга Смирнова", "Кирилл Андреев", "Нина Павлова"];

    var DEMO_USERS = [
        {
            id: "user-student",
            role: ROLE_TRADER,
            name: "Студент",
            email: "student@cryptotrade.local",
            password: "student123",
            balanceUsd: START_BALANCE,
            createdAt: DEMO_CREATED_AT
        },
        {
            id: "user-admin",
            role: ROLE_ADMIN,
            name: "Администратор",
            email: "admin@cryptotrade.local",
            password: "admin123",
            balanceUsd: START_BALANCE,
            createdAt: DEMO_CREATED_AT
        }
    ];

    var DEFAULT_CURRENCIES = [
        {
            id: "btc",
            symbol: "BTC",
            name: "Bitcoin",
            price: 68120.5,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "BTCUSDT",
            color: "#f7931a",
            risk: "Высокий",
            description: "Крупнейшая криптовалюта с высокой ликвидностью и заметной волатильностью.",
            history: [61200, 62840, 62110, 63620, 64880, 64190, 65300, 66780, 65940, 67120, 67580, 68120.5]
        },
        {
            id: "eth",
            symbol: "ETH",
            name: "Ethereum",
            price: 3520.75,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "ETHUSDT",
            color: "#627eea",
            risk: "Средний",
            description: "Платформа смарт-контрактов, используемая для DeFi, NFT и приложений Web3.",
            history: [3080, 3165, 3210, 3188, 3275, 3330, 3295, 3375, 3420, 3465, 3490, 3520.75]
        },
        {
            id: "sol",
            symbol: "SOL",
            name: "Solana",
            price: 154.32,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "SOLUSDT",
            color: "#14f195",
            risk: "Высокий",
            description: "Высокопроизводительная сеть для быстрых транзакций и децентрализованных приложений.",
            history: [128, 132, 139, 136, 142, 146, 143, 149, 151, 150, 153, 154.32]
        },
        {
            id: "ada",
            symbol: "ADA",
            name: "Cardano",
            price: 0.48,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "ADAUSDT",
            color: "#2a71d0",
            risk: "Средний",
            description: "Блокчейн-платформа с акцентом на исследовательский подход и устойчивость.",
            history: [0.42, 0.43, 0.44, 0.435, 0.45, 0.455, 0.46, 0.452, 0.466, 0.472, 0.476, 0.48]
        },
        {
            id: "bnb",
            symbol: "BNB",
            name: "BNB",
            price: 598.4,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "BNBUSDT",
            color: "#f3ba2f",
            risk: "Средний",
            description: "Монета экосистемы Binance, используемая для комиссий, сервисов и DeFi-приложений.",
            history: [548, 556, 571, 566, 579, 584, 576, 588, 593, 590, 596, 598.4]
        },
        {
            id: "xrp",
            symbol: "XRP",
            name: "XRP",
            price: 0.52,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "XRPUSDT",
            color: "#23292f",
            risk: "Средний",
            description: "Актив сети XRP Ledger, ориентированной на быстрые переводы и платежную инфраструктуру.",
            history: [0.47, 0.482, 0.49, 0.485, 0.498, 0.505, 0.499, 0.511, 0.516, 0.512, 0.519, 0.52]
        },
        {
            id: "doge",
            symbol: "DOGE",
            name: "Dogecoin",
            price: 0.14,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "DOGEUSDT",
            color: "#c2a633",
            risk: "Высокий",
            description: "Популярная мем-криптовалюта с высокой волатильностью и активным сообществом.",
            history: [0.118, 0.124, 0.121, 0.129, 0.132, 0.128, 0.135, 0.138, 0.136, 0.142, 0.139, 0.14]
        },
        {
            id: "avax",
            symbol: "AVAX",
            name: "Avalanche",
            price: 31.6,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "AVAXUSDT",
            color: "#e84142",
            risk: "Высокий",
            description: "Платформа для смарт-контрактов и быстрых блокчейн-сетей с поддержкой подсетей.",
            history: [26.8, 27.4, 28.1, 27.9, 29.2, 30.1, 29.7, 30.4, 31.0, 30.8, 31.4, 31.6]
        },
        {
            id: "dot",
            symbol: "DOT",
            name: "Polkadot",
            price: 6.85,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "DOTUSDT",
            color: "#e6007a",
            risk: "Средний",
            description: "Сеть для взаимодействия блокчейнов, парачейнов и кроссчейн-приложений.",
            history: [5.92, 6.08, 6.01, 6.22, 6.35, 6.28, 6.44, 6.58, 6.51, 6.72, 6.79, 6.85]
        },
        {
            id: "link",
            symbol: "LINK",
            name: "Chainlink",
            price: 15.9,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "LINKUSDT",
            color: "#2a5ada",
            risk: "Средний",
            description: "Оракульная сеть для передачи внешних данных в смарт-контракты.",
            history: [13.8, 14.1, 13.95, 14.35, 14.8, 14.62, 15.05, 15.3, 15.18, 15.55, 15.72, 15.9]
        },
        {
            id: "ltc",
            symbol: "LTC",
            name: "Litecoin",
            price: 84.2,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "LTCUSDT",
            color: "#345d9d",
            risk: "Средний",
            description: "Один из ранних криптоактивов, ориентированный на быстрые и недорогие переводы.",
            history: [76.2, 77.5, 78.1, 77.8, 79.6, 80.4, 81.2, 80.9, 82.5, 83.1, 83.7, 84.2]
        },
        {
            id: "trx",
            symbol: "TRX",
            name: "TRON",
            price: 0.115,
            priceMode: PRICE_MODE_AUTO,
            source: PRICE_SOURCE_BINANCE,
            marketSymbol: "TRXUSDT",
            color: "#ff0013",
            risk: "Средний",
            description: "Блокчейн-сеть для быстрых переводов токенов и децентрализованных приложений.",
            history: [0.101, 0.104, 0.103, 0.107, 0.109, 0.108, 0.111, 0.112, 0.1115, 0.113, 0.114, 0.115]
        }
    ];

    var COLOR_PALETTE = ["#f7931a", "#627eea", "#14f195", "#2a71d0", "#e84142", "#00a3ff", "#8a63d2", "#21a67a"];

    function readStorage(key) {
        try {
            return localStorage.getItem(key);
        } catch (error) {
            return null;
        }
    }

    function writeStorage(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (error) {
            return false;
        }

        return true;
    }

    function removeStorage(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            return false;
        }

        return true;
    }

    function isDatabaseKey(key) {
        return key === USERS_KEY || key === DATA_KEY;
    }

    function canUseBackendApi() {
        return typeof XMLHttpRequest !== "undefined" && window.location && window.location.protocol !== "file:";
    }

    function apiRequest(method, path, payload) {
        var request;

        if (!canUseBackendApi()) {
            return null;
        }

        try {
            request = new XMLHttpRequest();
            request.open(method, path, false);
            request.setRequestHeader("Accept", "application/json");

            if (payload) {
                request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            }

            request.send(payload ? JSON.stringify(payload) : null);

            if (request.status < 200 || request.status >= 300) {
                databaseAvailable = false;
                return null;
            }

            databaseAvailable = true;
            return JSON.parse(request.responseText || "{}");
        } catch (error) {
            databaseAvailable = false;
            return null;
        }
    }

    function apiFetchJson(path) {
        if (!canUseBackendApi() || typeof fetch !== "function") {
            return Promise.resolve(null);
        }

        return fetch(path, {
            cache: "no-store",
            headers: {
                Accept: "application/json"
            }
        }).then(function (response) {
            if (!response.ok) {
                return null;
            }

            return response.json();
        }).catch(function () {
            return null;
        });
    }

    function intervalForTimeframe(timeframe) {
        var map = {
            "1": "1m",
            "5": "5m",
            "15": "15m",
            "60": "1h"
        };

        return map[String(timeframe || "1")] || "1m";
    }

    function defaultDatabaseState() {
        return {
            users: null,
            data: null
        };
    }

    function getDatabaseState() {
        var response;

        if (databaseStateCache) {
            return databaseStateCache;
        }

        response = apiRequest("GET", API_STATE_URL);

        if (!response || !response.data || !Array.isArray(response.users)) {
            return defaultDatabaseState();
        }

        databaseStateCache = {
            users: response.users,
            data: response.data
        };
        return databaseStateCache;
    }

    function saveDatabaseState() {
        var response;

        if (!databaseStateCache) {
            return false;
        }

        response = apiRequest("POST", API_STATE_URL, databaseStateCache);

        if (response && response.ok && response.state) {
            databaseStateCache = response.state;
            return true;
        }

        return false;
    }

    function readJson(key, fallback) {
        var state;
        var rawValue = readStorage(key);

        if (isDatabaseKey(key) && canUseBackendApi()) {
            state = getDatabaseState();

            if (key === USERS_KEY) {
                return Array.isArray(state.users) ? state.users : fallback;
            }

            if (key === DATA_KEY) {
                return state.data && typeof state.data === "object" ? state.data : fallback;
            }
        }

        if (!rawValue) {
            return fallback;
        }

        try {
            return JSON.parse(rawValue);
        } catch (error) {
            return fallback;
        }
    }

    function writeJson(key, value) {
        var state;

        if (isDatabaseKey(key) && canUseBackendApi()) {
            state = getDatabaseState();

            if (key === USERS_KEY) {
                state.users = value;
            }

            if (key === DATA_KEY) {
                state.data = value;
            }

            databaseStateCache = state;
            return saveDatabaseState();
        }

        return writeStorage(key, JSON.stringify(value));
    }

    function normalizeEmail(email) {
        return String(email || "").trim().toLowerCase();
    }

    function normalizeSymbol(symbol) {
        return String(symbol || "").trim().toUpperCase();
    }

    function normalizeMarketSymbol(symbol) {
        return normalizeSymbol(symbol).replace(/[^A-Z0-9]/g, "");
    }

    function normalizeId(value) {
        return String(value || "")
            .trim()
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-|-$/g, "");
    }

    function createId(prefix) {
        return prefix + "-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 7);
    }

    function roundMoney(value) {
        return Math.round((Number(value) || 0) * 100) / 100;
    }

    function roundPrice(value) {
        return Math.round((Number(value) || 0) * 1000000) / 1000000;
    }

    function roundAmount(value) {
        return Math.round((Number(value) || 0) * 100000000) / 100000000;
    }

    function formatMoney(value) {
        return "$" + Number(value || 0).toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function formatPrice(value) {
        var price = Number(value) || 0;

        if (price < 1) {
            return "$" + price.toLocaleString("en-US", {
                minimumFractionDigits: 4,
                maximumFractionDigits: 6
            });
        }

        return formatMoney(price);
    }

    function formatAmount(value) {
        return Number(value || 0).toLocaleString("en-US", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 8
        });
    }

    function formatPercent(value) {
        var number = Number(value) || 0;
        var sign = number > 0 ? "+" : "";

        return sign + number.toFixed(2) + "%";
    }

    function formatDate(value) {
        var date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return "";
        }

        return date.toLocaleString("ru-RU", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    function escapeHtml(value) {
        return String(value == null ? "" : value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function safeColor(color) {
        return /^#[0-9a-f]{6}$/i.test(String(color || "")) ? color : "#0f9f6e";
    }

    function setText(selector, value) {
        var element = document.querySelector(selector);

        if (element) {
            element.textContent = value;
        }
    }

    function showFlash(message, type) {
        var holder = document.querySelector("[data-flash]");

        if (!holder) {
            return;
        }

        var flash = document.createElement("div");
        flash.className = "flash " + (type || "success");
        flash.textContent = message;
        holder.innerHTML = "";
        holder.appendChild(flash);
    }

    function cloneDemoUsers() {
        return DEMO_USERS.map(function (user) {
            return Object.assign({}, user);
        });
    }

    function normalizeUser(user) {
        var normalized = Object.assign({}, user);
        var role = String(normalized.role || ROLE_TRADER).trim().toLowerCase();
        normalized.id = normalized.id || createId("user");
        normalized.role = [ROLE_TRADER, ROLE_ADMIN, ROLE_SIMULATOR].indexOf(role) === -1 ? ROLE_TRADER : role;
        normalized.name = String(normalized.name || "Пользователь").trim();
        normalized.email = normalizeEmail(normalized.email);
        normalized.password = String(normalized.password || "");
        normalized.balanceUsd = Number.isFinite(Number(normalized.balanceUsd)) ? Number(normalized.balanceUsd) : START_BALANCE;
        normalized.createdAt = normalized.createdAt || new Date().toISOString();
        normalized.isSimulated = Boolean(normalized.isSimulated);
        if (normalized.isSimulated) {
            normalized.role = ROLE_SIMULATOR;
        }
        return normalized;
    }

    function loadUsers() {
        var users = readJson(USERS_KEY, null);
        var changed = false;

        if (!Array.isArray(users)) {
            users = cloneDemoUsers();
            changed = true;
        }

        users = users.map(normalizeUser).filter(function (user) {
            return user.email && user.password;
        });

        DEMO_USERS.forEach(function (demoUser) {
            var existingIndex = users.findIndex(function (user) {
                return normalizeEmail(user.email) === demoUser.email;
            });

            if (existingIndex === -1) {
                users.push(Object.assign({}, demoUser));
                changed = true;
                return;
            }

            var mergedUser = Object.assign({}, demoUser, users[existingIndex], {
                id: demoUser.id,
                role: demoUser.role,
                email: demoUser.email,
                password: demoUser.password,
                name: users[existingIndex].name || demoUser.name
            });

            if (JSON.stringify(users[existingIndex]) !== JSON.stringify(mergedUser)) {
                users[existingIndex] = mergedUser;
                changed = true;
            }
        });

        if (changed) {
            saveUsers(users);
        }

        return users;
    }

    function saveUsers(users) {
        writeJson(USERS_KEY, users);
    }

    function getUserById(userId) {
        return loadUsers().find(function (user) {
            return user.id === userId;
        }) || null;
    }

    function updateUser(updatedUser) {
        var users = loadUsers().map(function (user) {
            return user.id === updatedUser.id ? normalizeUser(updatedUser) : user;
        });

        saveUsers(users);
        return getUserById(updatedUser.id);
    }

    function getCurrentUser() {
        var session = readJson(SESSION_KEY, null);

        if (!session || !session.userId) {
            return null;
        }

        return getUserById(session.userId);
    }

    function saveSession(user) {
        writeJson(SESSION_KEY, {
            userId: user.id,
            startedAt: new Date().toISOString()
        });
    }

    function clearSession() {
        removeStorage(SESSION_KEY);
    }

    function getUserTarget(user) {
        return user.role === ROLE_ADMIN ? "admin.html" : "dashboard.html";
    }

    function redirectTo(path) {
        window.location.href = path;
    }

    function getCurrencyChange(currency) {
        var history = Array.isArray(currency.history) ? currency.history : [];

        if (history.length < 2) {
            return 0;
        }

        var previous = Number(history[history.length - 2]) || 0;
        var current = Number(history[history.length - 1]) || Number(currency.price) || 0;

        if (!previous) {
            return 0;
        }

        return ((current - previous) / previous) * 100;
    }

    function findDefaultCurrency(currency) {
        var id = normalizeId(currency && currency.id);
        var symbol = normalizeSymbol(currency && currency.symbol);

        return DEFAULT_CURRENCIES.find(function (item) {
            return normalizeId(item.id) === id || normalizeSymbol(item.symbol) === symbol;
        }) || null;
    }

    function normalizePriceMode(mode) {
        return mode === PRICE_MODE_AUTO ? PRICE_MODE_AUTO : PRICE_MODE_MANUAL;
    }

    function normalizeCurrency(currency, index) {
        var price = Number(currency.price) || 1;
        var history = Array.isArray(currency.history) && currency.history.length ? currency.history.map(Number) : buildHistory(price, index);
        var lastPrice = Number(history[history.length - 1]) || price;
        var symbol = normalizeSymbol(currency.symbol || "COIN");
        var defaults = findDefaultCurrency({
            id: currency.id,
            symbol: symbol
        });
        var priceMode = normalizePriceMode(currency.priceMode || (defaults && defaults.priceMode));
        var marketSymbol = normalizeMarketSymbol(currency.marketSymbol || currency.externalSymbol || (defaults && defaults.marketSymbol) || "");

        if (priceMode === PRICE_MODE_AUTO && !marketSymbol) {
            priceMode = PRICE_MODE_MANUAL;
        }

        return {
            id: normalizeId(currency.id || symbol || "asset-" + index),
            symbol: symbol,
            name: String(currency.name || symbol || "Актив").trim(),
            price: roundPrice(lastPrice),
            priceMode: priceMode,
            source: priceMode === PRICE_MODE_AUTO ? (currency.source || (defaults && defaults.source) || PRICE_SOURCE_BINANCE) : "manual",
            marketSymbol: marketSymbol,
            lastSyncAt: currency.lastSyncAt || "",
            lastSyncStatus: currency.lastSyncStatus || (priceMode === PRICE_MODE_AUTO ? "pending" : "manual"),
            lastSyncMessage: currency.lastSyncMessage || (priceMode === PRICE_MODE_AUTO ? "Ожидает синхронизации" : "Ручной курс администратора"),
            color: safeColor(currency.color || COLOR_PALETTE[index % COLOR_PALETTE.length]),
            risk: ["Низкий", "Средний", "Высокий"].indexOf(currency.risk) === -1 ? "Средний" : currency.risk,
            description: String(currency.description || "Учебный криптоактив для симуляции торгов.").trim(),
            history: history.slice(-30).map(function (value) {
                return roundPrice(value);
            })
        };
    }

    function mergeDefaultCurrencies(currencies) {
        var merged = currencies.slice();

        DEFAULT_CURRENCIES.forEach(function (defaultCurrency, index) {
            var exists = merged.some(function (currency) {
                return normalizeId(currency.id) === defaultCurrency.id || normalizeSymbol(currency.symbol) === defaultCurrency.symbol;
            });

            if (!exists) {
                merged.push(normalizeCurrency(defaultCurrency, merged.length + index));
            }
        });

        return merged;
    }

    function buildHistory(price, offset) {
        var factors = [0.91, 0.94, 0.925, 0.955, 0.97, 0.962, 0.985, 1.01, 0.995, 1.018, 1.026, 1];

        return factors.map(function (factor, index) {
            var wave = 1 + ((offset || 0) % 4) * 0.006 + index * 0.001;
            return roundPrice(price * factor * wave);
        });
    }

    function defaultData() {
        return {
            currencies: DEFAULT_CURRENCIES.map(normalizeCurrency),
            wallets: [],
            transactions: [],
            settings: defaultSettings()
        };
    }

    function defaultSettings() {
        return {
            simulationEnabled: false,
            simulationLevel: 35,
            lastSimulationAt: "",
            simulationUsersTarget: 4,
            simulationTradesPerMinute: 6,
            simulationCarry: 0
        };
    }

    function normalizeSettings(settings) {
        var normalized = Object.assign(defaultSettings(), settings || {});
        var level = Number(normalized.simulationLevel);
        var usersTarget = Number(normalized.simulationUsersTarget);
        var tradesPerMinute = Number(normalized.simulationTradesPerMinute);
        var carry = Number(normalized.simulationCarry);

        normalized.simulationEnabled = Boolean(normalized.simulationEnabled);
        normalized.simulationLevel = Math.max(0, Math.min(100, Number.isFinite(level) ? Math.round(level) : 35));
        normalized.lastSimulationAt = normalized.lastSimulationAt || "";
        normalized.simulationUsersTarget = Math.max(0, Math.min(200, Number.isFinite(usersTarget) ? Math.round(usersTarget) : Math.max(1, Math.min(12, Math.round(normalized.simulationLevel / 15) + 2))));
        normalized.simulationTradesPerMinute = Math.max(0, Math.min(600, Number.isFinite(tradesPerMinute) ? Math.round(tradesPerMinute) : Math.max(1, Math.round(normalized.simulationLevel / 8))));
        normalized.simulationCarry = Math.max(0, Number.isFinite(carry) ? carry : 0);
        return normalized;
    }

    function loadData() {
        var data = readJson(DATA_KEY, null);

        if (!data || typeof data !== "object") {
            data = defaultData();
            saveData(data);
            return data;
        }

        data.currencies = Array.isArray(data.currencies) && data.currencies.length
            ? data.currencies.map(normalizeCurrency)
            : DEFAULT_CURRENCIES.map(normalizeCurrency);
        data.currencies = mergeDefaultCurrencies(data.currencies);
        data.wallets = Array.isArray(data.wallets) ? data.wallets : [];
        data.transactions = Array.isArray(data.transactions) ? data.transactions : [];
        data.settings = normalizeSettings(data.settings);
        return data;
    }

    function saveData(data) {
        writeJson(DATA_KEY, data);
    }

    function getCurrency(data, currencyId) {
        return data.currencies.find(function (currency) {
            return currency.id === currencyId;
        }) || data.currencies[0] || null;
    }

    function getWallet(data, userId, currencyId) {
        var wallet = data.wallets.find(function (item) {
            return item.userId === userId && item.currencyId === currencyId;
        });

        if (!wallet) {
            wallet = {
                id: createId("wallet"),
                userId: userId,
                currencyId: currencyId,
                amount: 0,
                updatedAt: new Date().toISOString()
            };
            data.wallets.push(wallet);
        }

        wallet.amount = roundAmount(wallet.amount);
        return wallet;
    }

    function findWallet(data, userId, currencyId) {
        var wallet = data.wallets.find(function (item) {
            return item.userId === userId && item.currencyId === currencyId;
        });

        if (!wallet) {
            return {
                amount: 0
            };
        }

        wallet.amount = roundAmount(wallet.amount);
        return wallet;
    }

    function getUserWallets(data, userId) {
        return data.wallets.filter(function (wallet) {
            return wallet.userId === userId && Number(wallet.amount) > 0;
        });
    }

    function calculatePortfolio(user, data) {
        var cryptoValue = getUserWallets(data, user.id).reduce(function (sum, wallet) {
            var currency = getCurrency(data, wallet.currencyId);
            return sum + (currency ? Number(wallet.amount) * Number(currency.price) : 0);
        }, 0);

        return {
            cash: roundMoney(user.balanceUsd),
            crypto: roundMoney(cryptoValue),
            total: roundMoney(Number(user.balanceUsd) + cryptoValue),
            assetsCount: getUserWallets(data, user.id).length
        };
    }

    function isSimulatedRecord(record) {
        return Boolean(record && (record.isSimulated || String(record.id || "").indexOf(SIMULATION_PREFIX) === 0));
    }

    function cleanupSimulationData() {
        var data = loadData();
        var users = loadUsers().filter(function (user) {
            return !isSimulatedRecord(user);
        });

        data.wallets = data.wallets.filter(function (wallet) {
            return !isSimulatedRecord(wallet) && !String(wallet.userId || "").startsWith(SIMULATION_PREFIX);
        });
        data.transactions = data.transactions.filter(function (transaction) {
            return !isSimulatedRecord(transaction) && !String(transaction.userId || "").startsWith(SIMULATION_PREFIX);
        });
        data.settings = Object.assign(normalizeSettings(data.settings), {
            simulationEnabled: false,
            lastSimulationAt: ""
        });

        saveUsers(users);
        saveData(data);
        return { ok: true, message: "Симулируемые пользователи и операции удалены." };
    }

    function pruneSimulatedDataForUsers(data, allowedUserIds) {
        data.wallets = data.wallets.filter(function (wallet) {
            return !isSimulatedRecord(wallet) || allowedUserIds.indexOf(wallet.userId) !== -1;
        });
        data.transactions = data.transactions.filter(function (transaction) {
            return !isSimulatedRecord(transaction) || allowedUserIds.indexOf(transaction.userId) !== -1;
        });
    }

    function limitSimulatedRecords(records, limit) {
        var simulated = records.filter(isSimulatedRecord).sort(function (left, right) {
            return new Date(right.createdAt || 0).getTime() - new Date(left.createdAt || 0).getTime();
        });
        var keepIds = simulated.slice(0, limit).map(function (record) {
            return record.id;
        });

        return records.filter(function (record) {
            return !isSimulatedRecord(record) || keepIds.indexOf(record.id) !== -1;
        });
    }

    function trimSimulatedHistory(data) {
        data.transactions = limitSimulatedRecords(data.transactions, SIMULATION_HISTORY_LIMIT);
    }

    function ensureSimulationUsers(targetCount, data) {
        var users = loadUsers();
        var existing = users.filter(isSimulatedRecord);
        var target = Math.max(0, Math.min(200, Math.round(Number(targetCount) || 0)));
        var index;
        var user;

        for (index = existing.length; index < target; index += 1) {
            user = {
                id: SIMULATION_PREFIX + "user-" + index,
                role: ROLE_SIMULATOR,
                name: SIMULATION_NAMES[index % SIMULATION_NAMES.length],
                email: "sim" + (index + 1) + "@cryptotrade.local",
                password: "simulated",
                balanceUsd: START_BALANCE + index * 850,
                createdAt: new Date(Date.now() - (index + 1) * 86400000).toISOString(),
                isSimulated: true
            };
            users.push(user);
        }

        if (existing.length > target) {
            users = users.filter(function (candidate) {
                if (!isSimulatedRecord(candidate)) {
                    return true;
                }

                var number = Number(String(candidate.id).replace(SIMULATION_PREFIX + "user-", ""));
                return Number.isNaN(number) || number < target;
            });
        }

        existing = users.filter(isSimulatedRecord);
        existing.forEach(function (candidate) {
            candidate.role = ROLE_SIMULATOR;
            candidate.isSimulated = true;
        });
        saveUsers(users);

        if (data) {
            pruneSimulatedDataForUsers(data, existing.map(function (candidate) {
                return candidate.id;
            }));
        }

        return existing;
    }

    function randomItem(items) {
        return items[Math.floor(Math.random() * items.length)];
    }

    function generateSimulatedTransaction(data, users) {
        var user = randomItem(users);
        var currency = randomItem(data.currencies);
        var side = Math.random() > 0.45 ? "buy" : "sell";
        var price = Number(currency.price) || 1;
        var maxUsd = Math.max(12, Math.min(900, Number(user.balanceUsd || START_BALANCE) * 0.08));
        var quantity = roundAmount((Math.random() * maxUsd + 8) / price);
        var wallet = getWallet(data, user.id, currency.id);

        wallet.isSimulated = true;

        if (side === "sell" && wallet.amount < quantity) {
            wallet.amount = roundAmount(wallet.amount + quantity * (1.4 + Math.random()));
        }

        var total = roundMoney(quantity * price);

        if (side === "buy") {
            user.balanceUsd = roundMoney(Math.max(0, Number(user.balanceUsd) - total));
            wallet.amount = roundAmount(wallet.amount + quantity);
        } else {
            user.balanceUsd = roundMoney(Number(user.balanceUsd) + total);
            wallet.amount = roundAmount(Math.max(0, wallet.amount - quantity));
        }

        wallet.updatedAt = new Date().toISOString();

        var transaction = {
            id: SIMULATION_PREFIX + createId("transaction"),
            userId: user.id,
            currencyId: currency.id,
            side: side,
            quantity: quantity,
            price: price,
            total: total,
            status: "Исполнено",
            createdAt: new Date().toISOString(),
            isSimulated: true
        };

        data.transactions.push(transaction);
        return transaction;
    }

    function runSimulationTick(force) {
        var data = loadData();
        var settings = normalizeSettings(data.settings);
        var lastRun = settings.lastSimulationAt ? new Date(settings.lastSimulationAt).getTime() : 0;
        var count;
        var users;
        var generated = 0;
        var now = Date.now();
        var elapsedMs = lastRun ? Math.max(0, now - lastRun) : SIMULATION_TICK_INTERVAL_MS;
        var expectedTrades = settings.simulationCarry + (elapsedMs / 60000) * settings.simulationTradesPerMinute;

        if (!settings.simulationEnabled) {
            return { ok: true, generated: 0, message: "Симуляция выключена." };
        }

        if (!force && lastRun && elapsedMs > SIMULATION_RESUME_GRACE_MS) {
            users = ensureSimulationUsers(settings.simulationUsersTarget, data);
            trimSimulatedHistory(data);
            data.settings = Object.assign(settings, {
                lastSimulationAt: new Date(now).toISOString(),
                simulationCarry: 0
            });
            saveData(data);
            return {
                ok: true,
                generated: 0,
                resumed: true,
                message: "Симуляция продолжена без догоняющих сделок."
            };
        }

        users = ensureSimulationUsers(settings.simulationUsersTarget, data);
        count = force ? 1 : Math.floor(expectedTrades);

        if (!users.length || !data.currencies.length || count <= 0) {
            data.settings = Object.assign(settings, {
                lastSimulationAt: new Date(now).toISOString(),
                simulationCarry: force ? settings.simulationCarry : expectedTrades
            });
            saveData(data);
            return { ok: true, generated: 0, skipped: true, message: "Пока нет сделок для генерации." };
        }

        while (generated < count && users.length && data.currencies.length) {
            generateSimulatedTransaction(data, users);
            generated += 1;
        }

        trimSimulatedHistory(data);
        data.settings = Object.assign(settings, {
            lastSimulationAt: new Date(now).toISOString(),
            simulationCarry: force ? settings.simulationCarry : Math.max(0, expectedTrades - generated)
        });
        saveData(data);
        saveUsers(loadUsers().map(function (user) {
            var simulated = users.find(function (item) {
                return item.id === user.id;
            });
            return simulated || user;
        }));

        return {
            ok: true,
            generated: generated,
            message: "Симуляция добавила операций: " + generated + "."
        };
    }

    function updateSimulationSettings(enabled, level) {
        var data = loadData();
        var settings = normalizeSettings(data.settings);

        settings.simulationEnabled = Boolean(enabled);
        settings.simulationUsersTarget = Math.max(0, Math.min(200, Math.round(Number(level && level.usersCount != null ? level.usersCount : level) || 0)));
        settings.simulationTradesPerMinute = Math.max(0, Math.min(600, Math.round(Number(level && level.tradesPerMinute != null ? level.tradesPerMinute : settings.simulationTradesPerMinute) || 0)));
        settings.simulationLevel = Math.min(100, Math.round((settings.simulationUsersTarget / 200) * 50 + (settings.simulationTradesPerMinute / 600) * 50));
        settings.simulationCarry = 0;
        settings.lastSimulationAt = new Date().toISOString();
        data.settings = settings;
        saveData(data);

        if (!settings.simulationEnabled) {
            return cleanupSimulationData();
        }

        ensureSimulationUsers(settings.simulationUsersTarget, data);
        trimSimulatedHistory(data);
        saveData(data);
        return { ok: true, message: "Симуляция сохранена: " + settings.simulationUsersTarget + " пользователей, " + settings.simulationTradesPerMinute + " сделок/мин." };
    }

    function authenticate(email, password) {
        var normalizedEmail = normalizeEmail(email);

        return loadUsers().find(function (user) {
            return normalizeEmail(user.email) === normalizedEmail && user.password === password;
        }) || null;
    }

    function registerUser(name, email, password) {
        var users = loadUsers();
        var normalizedName = String(name || "").trim();
        var normalizedEmail = normalizeEmail(email);
        var rawPassword = String(password || "");
        var exists = users.some(function (user) {
            return normalizeEmail(user.email) === normalizedEmail;
        });

        if (normalizedName.length < 2) {
            return { ok: false, message: "Введите имя длиной не меньше 2 символов." };
        }

        if (!normalizedEmail) {
            return { ok: false, message: "Введите email." };
        }

        if (rawPassword.length < 6) {
            return { ok: false, message: "Пароль должен содержать минимум 6 символов." };
        }

        if (exists) {
            return { ok: false, message: "Пользователь с таким email уже зарегистрирован." };
        }

        var user = {
            id: createId("user"),
            role: ROLE_TRADER,
            name: normalizedName,
            email: normalizedEmail,
            password: rawPassword,
            balanceUsd: START_BALANCE,
            createdAt: new Date().toISOString()
        };

        users.push(user);
        saveUsers(users);
        return { ok: true, user: user };
    }

    function performTrade(userId, currencyId, side, quantityValue) {
        var data = loadData();
        var user = getUserById(userId);
        var currency = getCurrency(data, currencyId);
        var quantity = roundAmount(quantityValue);

        if (!user) {
            return { ok: false, message: "Сессия не найдена. Войдите снова." };
        }

        if (!currency) {
            return { ok: false, message: "Актив не найден." };
        }

        if (side !== "buy" && side !== "sell") {
            return { ok: false, message: "Неизвестный тип сделки." };
        }

        if (!quantity || quantity <= 0) {
            return { ok: false, message: "Количество должно быть больше нуля." };
        }

        var wallet = getWallet(data, user.id, currency.id);
        var total = roundMoney(quantity * currency.price);

        if (total <= 0) {
            return { ok: false, message: "Сумма сделки должна быть не меньше $0.01." };
        }

        if (side === "buy" && user.balanceUsd < total) {
            return { ok: false, message: "Недостаточно USD для покупки." };
        }

        if (side === "sell" && wallet.amount < quantity) {
            return { ok: false, message: "Недостаточно монет для продажи." };
        }

        if (side === "buy") {
            user.balanceUsd = roundMoney(user.balanceUsd - total);
            wallet.amount = roundAmount(wallet.amount + quantity);
        } else {
            user.balanceUsd = roundMoney(user.balanceUsd + total);
            wallet.amount = roundAmount(wallet.amount - quantity);
        }

        if (wallet.amount < 0.00000001) {
            wallet.amount = 0;
        }

        wallet.updatedAt = new Date().toISOString();

        var transaction = {
            id: createId("transaction"),
            userId: user.id,
            currencyId: currency.id,
            side: side,
            quantity: quantity,
            price: currency.price,
            total: total,
            status: "Исполнено",
            createdAt: new Date().toISOString()
        };

        data.transactions.push(transaction);
        saveData(data);
        updateUser(user);

        return {
            ok: true,
            message: side === "buy" ? "Покупка выполнена." : "Продажа выполнена.",
            user: user,
            data: data,
            transaction: transaction
        };
    }

    function addCurrency(symbol, name, priceValue, risk, description, priceModeValue, marketSymbolValue) {
        var data = loadData();
        var normalizedSymbol = normalizeSymbol(symbol);
        var normalizedName = String(name || "").trim();
        var price = roundPrice(priceValue);
        var priceMode = normalizePriceMode(priceModeValue);
        var marketSymbol = normalizeMarketSymbol(marketSymbolValue);
        var exists = data.currencies.some(function (currency) {
            return currency.symbol === normalizedSymbol;
        });

        if (!normalizedSymbol) {
            return { ok: false, message: "Введите символ монеты." };
        }

        if (!normalizedName) {
            return { ok: false, message: "Введите название монеты." };
        }

        if (!price || price <= 0) {
            return { ok: false, message: "Цена должна быть больше нуля." };
        }

        if (exists) {
            return { ok: false, message: "Актив с таким символом уже существует." };
        }

        if (priceMode === PRICE_MODE_AUTO && !marketSymbol) {
            return { ok: false, message: "Для автообновления укажите биржевую пару, например BTCUSDT." };
        }

        var currency = normalizeCurrency({
            id: normalizeId(normalizedSymbol),
            symbol: normalizedSymbol,
            name: normalizedName,
            price: price,
            priceMode: priceMode,
            source: priceMode === PRICE_MODE_AUTO ? PRICE_SOURCE_BINANCE : "manual",
            marketSymbol: marketSymbol,
            lastSyncStatus: priceMode === PRICE_MODE_AUTO ? "pending" : "manual",
            lastSyncMessage: priceMode === PRICE_MODE_AUTO ? "Ожидает синхронизации с Binance" : "Ручной курс администратора",
            color: COLOR_PALETTE[data.currencies.length % COLOR_PALETTE.length],
            risk: risk,
            description: description,
            history: buildHistory(price, data.currencies.length)
        }, data.currencies.length);

        data.currencies.push(currency);
        saveData(data);
        return { ok: true, currency: currency, message: "Актив добавлен." };
    }

    function updateCurrencyPrice(currencyId, priceValue, priceModeValue, marketSymbolValue) {
        var data = loadData();
        var currency = getCurrency(data, currencyId);
        var price = roundPrice(priceValue);
        var priceMode = normalizePriceMode(priceModeValue);
        var marketSymbol = normalizeMarketSymbol(marketSymbolValue);

        if (!currency) {
            return { ok: false, message: "Актив не найден." };
        }

        if (!price || price <= 0) {
            return { ok: false, message: "Цена должна быть больше нуля." };
        }

        if (priceMode === PRICE_MODE_AUTO && !marketSymbol) {
            return { ok: false, message: "Для автообновления укажите биржевую пару, например BTCUSDT." };
        }

        currency.price = price;
        currency.priceMode = priceMode;
        currency.source = priceMode === PRICE_MODE_AUTO ? PRICE_SOURCE_BINANCE : "manual";
        currency.marketSymbol = marketSymbol;
        currency.lastSyncAt = priceMode === PRICE_MODE_AUTO ? currency.lastSyncAt : new Date().toISOString();
        currency.lastSyncStatus = priceMode === PRICE_MODE_AUTO ? "pending" : "manual";
        currency.lastSyncMessage = priceMode === PRICE_MODE_AUTO ? "Ожидает синхронизации с Binance" : "Ручной курс администратора";
        currency.history = (currency.history || []).concat(price).slice(-30);
        saveData(data);
        return {
            ok: true,
            currency: currency,
            message: priceMode === PRICE_MODE_AUTO ? "Настройки автообновления сохранены." : "Курс обновлен вручную."
        };
    }

    function getAutoSyncTargets(data) {
        return data.currencies.filter(function (currency) {
            return currency.priceMode === PRICE_MODE_AUTO && normalizeMarketSymbol(currency.marketSymbol);
        });
    }

    function getUniqueMarketSymbols(currencies) {
        var symbols = [];

        currencies.forEach(function (currency) {
            var symbol = normalizeMarketSymbol(currency.marketSymbol);

            if (symbol && symbols.indexOf(symbol) === -1) {
                symbols.push(symbol);
            }
        });

        return symbols;
    }

    function getSyncMeta() {
        var meta = readJson(PRICE_SYNC_KEY, {});

        return meta && typeof meta === "object" ? meta : {};
    }

    function saveSyncMeta(meta) {
        writeJson(PRICE_SYNC_KEY, meta);
    }

    function shouldSkipSync(force) {
        var meta = getSyncMeta();
        var lastAttempt = meta.lastAttemptAt ? new Date(meta.lastAttemptAt).getTime() : 0;

        return !force && lastAttempt && Date.now() - lastAttempt < PRICE_SYNC_INTERVAL_MS;
    }

    function buildBinanceTickerUrl(symbols) {
        return BINANCE_TICKER_URL + "?symbols=" + encodeURIComponent(JSON.stringify(symbols)) + "&type=MINI";
    }

    function updateCurrencyFromTicker(currency, ticker, now) {
        var price = roundPrice(ticker && (ticker.lastPrice || ticker.price));

        if (!price || price <= 0) {
            currency.lastSyncStatus = "error";
            currency.lastSyncMessage = "Цена по паре не найдена";
            return false;
        }

        currency.price = price;
        currency.source = PRICE_SOURCE_BINANCE;
        currency.priceMode = PRICE_MODE_AUTO;
        currency.lastSyncAt = now;
        currency.lastSyncStatus = "ok";
        currency.lastSyncMessage = "Binance Spot " + normalizeMarketSymbol(currency.marketSymbol);
        currency.history = (currency.history || []).concat(price).slice(-30);
        return true;
    }

    function syncMarketPrices(options) {
        var force = options && options.force;
        var data = loadData();
        var targets = getAutoSyncTargets(data);
        var symbols = getUniqueMarketSymbols(targets);
        var now = new Date().toISOString();

        if (!targets.length || !symbols.length) {
            return Promise.resolve({ ok: true, updated: 0, message: "Нет активов в автоматическом режиме." });
        }

        if (shouldSkipSync(force)) {
            return Promise.resolve({ ok: true, skipped: true, updated: 0, message: "Курсы уже обновлялись меньше минуты назад." });
        }

        if (typeof fetch !== "function") {
            return Promise.resolve({ ok: false, updated: 0, message: "Браузер не поддерживает загрузку внешних курсов." });
        }

        saveSyncMeta(Object.assign({}, getSyncMeta(), {
            lastAttemptAt: now
        }));

        return fetch(buildBinanceTickerUrl(symbols), {
            cache: "no-store"
        }).then(function (response) {
            if (!response.ok) {
                throw new Error("HTTP " + response.status);
            }

            return response.json();
        }).then(function (payload) {
            var rows = Array.isArray(payload) ? payload : [payload];
            var tickerBySymbol = {};
            var updated = 0;
            var missing = 0;

            rows.forEach(function (row) {
                tickerBySymbol[normalizeMarketSymbol(row && row.symbol)] = row;
            });

            targets.forEach(function (currency) {
                var symbol = normalizeMarketSymbol(currency.marketSymbol);
                var ticker = tickerBySymbol[symbol];

                if (ticker && updateCurrencyFromTicker(currency, ticker, now)) {
                    updated += 1;
                    return;
                }

                missing += 1;
                currency.lastSyncStatus = "error";
                currency.lastSyncMessage = "Пара " + symbol + " не найдена у Binance";
            });

            saveData(data);
            saveSyncMeta({
                lastAttemptAt: now,
                lastSuccessAt: updated ? now : getSyncMeta().lastSuccessAt || "",
                updated: updated,
                missing: missing
            });

            return {
                ok: updated > 0,
                updated: updated,
                missing: missing,
                message: updated
                    ? "Автообновление выполнено: " + updated + " актив(ов)."
                    : "Автообновление не нашло подходящих пар."
            };
        }).catch(function (error) {
            targets.forEach(function (currency) {
                currency.lastSyncStatus = "error";
                currency.lastSyncMessage = "Источник недоступен: " + error.message;
            });
            saveData(data);
            saveSyncMeta(Object.assign({}, getSyncMeta(), {
                lastAttemptAt: now,
                lastErrorAt: now,
                lastError: error.message
            }));

            return {
                ok: false,
                updated: 0,
                message: "Не удалось обновить курсы из Binance: " + error.message
            };
        });
    }

    function getInitialTheme() {
        var savedTheme = readStorage(THEME_KEY);

        if (savedTheme === DARK_THEME || savedTheme === LIGHT_THEME) {
            return savedTheme;
        }

        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return DARK_THEME;
        }

        return LIGHT_THEME;
    }

    function applyTheme(theme, button) {
        document.documentElement.dataset.theme = theme;
        document.body.dataset.theme = theme;
        writeStorage(THEME_KEY, theme);

        if (button) {
            var isDark = theme === DARK_THEME;
            button.textContent = isDark ? "Светлая тема" : "Темная тема";
            button.setAttribute("aria-pressed", String(isDark));
        }
    }

    function initThemeToggle() {
        var accountChip = document.querySelector(".account-chip");

        if (!accountChip) {
            return;
        }

        var button = document.createElement("button");
        button.className = "theme-toggle";
        button.type = "button";
        button.setAttribute("aria-label", "Переключить тему");

        applyTheme(getInitialTheme(), button);

        button.addEventListener("click", function () {
            var nextTheme = document.body.dataset.theme === DARK_THEME ? LIGHT_THEME : DARK_THEME;
            applyTheme(nextTheme, button);
        });

        accountChip.appendChild(button);
    }

    function initAuthSwitcher() {
        var panels = document.querySelectorAll("[data-auth-panel]");
        var buttons = document.querySelectorAll("[data-auth-open]");

        if (!panels.length || !buttons.length) {
            return;
        }

        function openPanel(panelName) {
            panels.forEach(function (panel) {
                panel.classList.toggle("is-hidden", panel.dataset.authPanel !== panelName);
            });
        }

        buttons.forEach(function (button) {
            button.addEventListener("click", function () {
                openPanel(button.dataset.authOpen);
            });
        });
    }

    function initLoginForm() {
        var form = document.querySelector("[data-login-form]");

        if (!form) {
            return;
        }

        form.addEventListener("submit", function (event) {
            event.preventDefault();

            var user = authenticate(form.elements.email.value, form.elements.password.value);

            if (!user) {
                showFlash("Неверный email или пароль.", "error");
                return;
            }

            saveSession(user);
            redirectTo(getUserTarget(user));
        });
    }

    function initRegisterForm() {
        var form = document.querySelector("[data-register-form]");

        if (!form) {
            return;
        }

        form.addEventListener("submit", function (event) {
            event.preventDefault();

            var result = registerUser(form.elements.name.value, form.elements.email.value, form.elements.password.value);

            if (!result.ok) {
                showFlash(result.message, "error");
                return;
            }

            saveSession(result.user);
            redirectTo("dashboard.html");
        });
    }

    function isPublicPage(page) {
        return page === "index" || page === "privacy" || page === "terms";
    }

    function initSessionUi() {
        var page = document.body.dataset.page;
        var user = getCurrentUser();

        if (page === "index") {
            if (user) {
                redirectTo(getUserTarget(user));
            }

            return null;
        }

        if (isPublicPage(page)) {
            return user;
        }

        if (!user) {
            redirectTo("index.html");
            return null;
        }

        if (page === "admin" && user.role !== ROLE_ADMIN) {
            redirectTo("dashboard.html");
            return null;
        }

        document.querySelectorAll("[data-admin-only]").forEach(function (element) {
            element.classList.toggle("is-hidden", user.role !== ROLE_ADMIN);
        });

        var activeNav = document.querySelector('[data-nav="' + page + '"]');

        if (activeNav) {
            activeNav.classList.add("active");
        }

        setText("[data-account-name]", user.name);
        setText("[data-dashboard-name]", user.name);

        var logoutButton = document.querySelector("[data-logout]");

        if (logoutButton) {
            logoutButton.addEventListener("click", function () {
                clearSession();
                redirectTo("index.html");
            });
        }

        return user;
    }

    function getPriceModeLabel(currency) {
        return currency.priceMode === PRICE_MODE_AUTO ? "Авто" : "Ручной";
    }

    function getPriceSourceLabel(currency) {
        if (currency.priceMode !== PRICE_MODE_AUTO) {
            return "Администратор";
        }

        return "Binance Spot" + (currency.marketSymbol ? " / " + currency.marketSymbol : "");
    }

    function getSyncStatusLabel(currency) {
        if (currency.priceMode !== PRICE_MODE_AUTO) {
            return "Ручной курс";
        }

        if (currency.lastSyncStatus === "ok" && currency.lastSyncAt) {
            return "Обновлено " + formatDate(currency.lastSyncAt);
        }

        return currency.lastSyncMessage || "Ожидает обновления";
    }

    function renderPriceSyncStatus() {
        var holders = document.querySelectorAll("[data-price-sync-status]");

        if (!holders.length) {
            return;
        }

        var data = loadData();
        var autoCurrencies = getAutoSyncTargets(data);
        var latestSync = autoCurrencies.reduce(function (latest, currency) {
            var time = currency.lastSyncAt ? new Date(currency.lastSyncAt).getTime() : 0;
            return time > latest ? time : latest;
        }, 0);
        var status = "";

        if (!autoCurrencies.length) {
            status = "Курсы задаются администратором.";
        } else if (latestSync) {
            status = "Рыночные данные обновляются автоматически.";
        } else {
            status = "Рыночные данные загружаются автоматически.";
        }

        holders.forEach(function (holder) {
            holder.textContent = status;
        });
    }

    function notifyPricesUpdated() {
        var event;

        renderPriceSyncStatus();

        if (typeof CustomEvent === "function") {
            event = new CustomEvent("cryptotrade:prices-updated");
        } else {
            event = document.createEvent("CustomEvent");
            event.initCustomEvent("cryptotrade:prices-updated", false, false, {});
        }

        document.dispatchEvent(event);
    }

    function notifySimulationUpdated() {
        var event;

        renderMarketActivity("[data-market-activity]", 8);

        if (typeof CustomEvent === "function") {
            event = new CustomEvent("cryptotrade:simulation-updated");
        } else {
            event = document.createEvent("CustomEvent");
            event.initCustomEvent("cryptotrade:simulation-updated", false, false, {});
        }

        document.dispatchEvent(event);
    }

    function refreshPriceDependentViews(page) {
        var user = getCurrentUser();

        renderMarketCards("[data-auth-market]", 4);
        renderPriceSyncStatus();

        if (page === "index") {
            return;
        }

        if (!user) {
            return;
        }

        if (page === "dashboard") {
            renderDashboardPage(user);
        }

        if (page === "market") {
            renderMarketTable();
        }

        if (page === "portfolio") {
            renderPortfolioPage(user);
        }

        if (page === "admin") {
            renderAdminTables();
        }

        notifyPricesUpdated();
    }

    function refreshSimulationViews(page) {
        var user = getCurrentUser();

        if (!user) {
            renderMarketActivity("[data-market-activity]", 8);
            return;
        }

        if (page === "dashboard") {
            renderDashboardPage(user);
        }

        if (page === "market") {
            renderMarketTable();
        }

        if (page === "admin") {
            renderAdminTables();
        }

        renderMarketActivity("[data-market-activity]", 8);
        notifySimulationUpdated();
    }

    function initSimulationAutoRefresh(page) {
        var activePages = ["dashboard", "market", "trade", "portfolio", "history", "admin"];

        if (activePages.indexOf(page) === -1) {
            return;
        }

        function run(force) {
            var result = runSimulationTick(force);

            if (result.generated) {
                refreshSimulationViews(page);
            }
        }

        run(false);
        window.setInterval(function () {
            run(false);
        }, SIMULATION_TICK_INTERVAL_MS);
    }

    function initPriceAutoRefresh(page) {
        var refreshPages = ["index", "dashboard", "market", "trade", "portfolio", "admin"];

        renderPriceSyncStatus();

        if (refreshPages.indexOf(page) === -1) {
            return;
        }

        function run(force) {
            syncMarketPrices({ force: force }).then(function (result) {
                if (result.updated) {
                    refreshPriceDependentViews(page);
                    return;
                }

                renderPriceSyncStatus();
            });
        }

        run(false);
        window.setInterval(function () {
            run(false);
        }, PRICE_SYNC_INTERVAL_MS);
    }

    function trendClass(currency) {
        return getCurrencyChange(currency) >= 0 ? "up" : "down";
    }

    function currencyDot(currency, extraClass) {
        return '<span class="coin-dot ' + (extraClass || "") + '" style="--coin: ' + safeColor(currency.color) + '"></span>';
    }

    function renderMarketActivity(selector, limit) {
        var container = document.querySelector(selector);

        if (!container) {
            return;
        }

        var data = loadData();
        var users = loadUsers();
        var transactions = data.transactions.slice().reverse().slice(0, limit || 8);

        if (!transactions.length) {
            container.innerHTML = '<div class="empty-state small"><h2>Активности пока нет</h2><p class="muted">После сделок здесь появится общая лента рынка.</p></div>';
            return;
        }

        container.innerHTML = transactions.map(function (transaction) {
            var currency = getCurrency(data, transaction.currencyId);
            var user = users.find(function (candidate) {
                return candidate.id === transaction.userId;
            });
            var userName = user ? user.name : "Участник";
            var simulationBadge = transaction.isSimulated ? '<span class="risk mini">Симуляция</span>' : "";

            return [
                '<div class="activity-row market-activity-row">',
                currency ? currencyDot(currency) : "",
                '<div><strong>' + escapeHtml(userName) + ' - ' + (transaction.side === "buy" ? "покупка" : "продажа") + ' ' + escapeHtml(currency ? currency.symbol : "") + '</strong>',
                '<small>' + formatAmount(transaction.quantity) + ' на ' + formatMoney(transaction.total) + ' · ' + formatDate(transaction.createdAt) + '</small></div>',
                simulationBadge,
                '</div>'
            ].join("");
        }).join("");
    }

    function renderMarketCards(selector, limit) {
        var container = document.querySelector(selector);

        if (!container) {
            return;
        }

        var currencies = loadData().currencies.slice(0, limit || 4);

        container.innerHTML = currencies.map(function (currency) {
            return [
                '<article class="market-card">',
                '<div class="coin-cell">',
                currencyDot(currency),
                '<div><strong>' + escapeHtml(currency.symbol) + '</strong><small>' + escapeHtml(currency.name) + '</small></div>',
                '</div>',
                '<strong class="price">' + formatPrice(currency.price) + '</strong>',
                '<span class="trend ' + trendClass(currency) + '">' + formatPercent(getCurrencyChange(currency)) + '</span>',
                '</article>'
            ].join("");
        }).join("");
    }

    function renderMarketTable() {
        var table = document.querySelector("[data-market-table]");

        if (!table) {
            return;
        }

        var data = loadData();

        table.innerHTML = data.currencies.map(function (currency) {
            return [
                '<tr>',
                '<td><div class="coin-cell">',
                currencyDot(currency),
                '<div><strong>' + escapeHtml(currency.symbol) + '</strong><small>' + escapeHtml(currency.name) + '</small></div>',
                '</div></td>',
                '<td>' + formatPrice(currency.price) + '</td>',
                '<td><span class="trend ' + trendClass(currency) + '">' + formatPercent(getCurrencyChange(currency)) + '</span></td>',
                '<td><span class="risk">' + escapeHtml(currency.risk) + '</span></td>',
                '<td><span class="risk">' + escapeHtml(getPriceModeLabel(currency)) + '</span><small>' + escapeHtml(getPriceSourceLabel(currency)) + '</small></td>',
                '<td><canvas class="line-chart mini" data-chart-currency="' + escapeHtml(currency.id) + '"></canvas></td>',
                '<td><a class="button compact" href="trade.html?currency=' + encodeURIComponent(currency.id) + '">Торговать</a></td>',
                '</tr>'
            ].join("");
        }).join("");

        drawCurrencyCharts();
        renderMarketActivity("[data-market-activity]", 10);
    }

    function renderDashboardPage(user) {
        var data = loadData();
        var portfolio = calculatePortfolio(user, data);
        var recent = document.querySelector("[data-recent-transactions]");

        setText("[data-total-value]", formatMoney(portfolio.total));
        setText("[data-cash-value]", formatMoney(portfolio.cash));
        setText("[data-assets-count]", String(portfolio.assetsCount));
        renderMarketCards("[data-dashboard-market]", 4);
        renderMarketActivity("[data-market-activity]", 6);
        drawChart(document.querySelector("[data-btc-chart]"), getCurrency(data, "btc"), {
            timeframe: "15"
        });

        if (recent) {
            var transactions = data.transactions
                .filter(function (transaction) {
                    return transaction.userId === user.id;
                })
                .slice()
                .reverse()
                .slice(0, 5);

            if (!transactions.length) {
                recent.innerHTML = '<div class="empty-state small"><h2>Сделок пока нет</h2><p class="muted">Первая операция появится здесь после покупки или продажи.</p></div>';
                return;
            }

            recent.innerHTML = transactions.map(function (transaction) {
                var currency = getCurrency(data, transaction.currencyId);
                return [
                    '<div class="activity-row">',
                    currency ? currencyDot(currency) : "",
                    '<div><strong>' + (transaction.side === "buy" ? "Покупка" : "Продажа") + ' ' + escapeHtml(currency ? currency.symbol : "") + '</strong>',
                    '<small>' + formatAmount(transaction.quantity) + ' на ' + formatMoney(transaction.total) + '</small></div>',
                    '</div>'
                ].join("");
            }).join("");
        }
    }

    function getRequestedCurrencyId() {
        try {
            return new URLSearchParams(window.location.search).get("currency");
        } catch (error) {
            return null;
        }
    }

    function initTradePage(user) {
        var select = document.querySelector("[data-trade-currency]");
        var form = document.querySelector("[data-trade-form]");
        var quantityInput = form ? form.elements.quantity : null;
        var chartType = document.querySelector("[data-chart-type]");
        var chartTimeframe = document.querySelector("[data-chart-timeframe]");
        var chartSma = document.querySelector("[data-chart-sma]");

        if (!select || !form || !quantityInput) {
            return;
        }

        var data = loadData();
        select.innerHTML = data.currencies.map(function (currency) {
            return '<option value="' + escapeHtml(currency.id) + '">' + escapeHtml(currency.symbol) + ' - ' + escapeHtml(currency.name) + '</option>';
        }).join("");

        var requestedCurrencyId = getRequestedCurrencyId();

        if (requestedCurrencyId && getCurrency(data, requestedCurrencyId)) {
            select.value = requestedCurrencyId;
        } else if (!select.value && data.currencies[0]) {
            select.value = data.currencies[0].id;
        }

        var activeUser = null;
        var activeData = null;
        var activeCurrency = null;
        var activeWallet = {
            amount: 0
        };

        function refreshTradeState(liveCurrency) {
            activeUser = getCurrentUser();
            activeData = loadData();
            activeCurrency = liveCurrency && liveCurrency.id === select.value
                ? liveCurrency
                : getCurrency(activeData, select.value);
            activeWallet = activeUser && activeCurrency
                ? findWallet(activeData, activeUser.id, activeCurrency.id)
                : { amount: 0 };
        }

        function updateTradeSummary(liveCurrency, useCachedState) {
            if (!useCachedState) {
                refreshTradeState(liveCurrency);
            }

            if (!activeUser || !activeCurrency) {
                return;
            }

            var quantity = Number(quantityInput.value) || 0;

            setText("[data-trade-pair]", activeCurrency.symbol + " / USD");
            setText("[data-trade-price]", formatPrice(activeCurrency.price));
            setText("[data-trade-description]", activeCurrency.description);
            setText("[data-trade-cash]", formatMoney(activeUser.balanceUsd));
            setText("[data-trade-wallet-symbol]", activeCurrency.symbol);
            setText("[data-trade-wallet]", formatAmount(activeWallet.amount));
            setText("[data-trade-total]", formatMoney(quantity * activeCurrency.price));
            setText("[data-trade-symbol]", activeCurrency.symbol);
            setText("[data-trade-risk]", activeCurrency.risk);

            var dot = document.querySelector("[data-trade-dot]");

            if (dot) {
                dot.style.setProperty("--coin", safeColor(activeCurrency.color));
            }
        }

        function renderTradeChart(force) {
            var freshData = loadData();
            var currency = getCurrency(freshData, select.value);
            var element = document.querySelector("[data-tv-chart]");
            var options = {
                type: chartType ? chartType.value : "candles",
                timeframe: chartTimeframe ? chartTimeframe.value : "1",
                showSma: chartSma ? chartSma.checked : true
            };

            if (!currency || !element) {
                return;
            }

            var cachedCandles = getCachedMarketCandles(currency, options.timeframe);

            if (cachedCandles) {
                applyMarketCandlesToCurrency(currency, cachedCandles, false);
            }

            drawAdvancedChart(element, currency, options);
            fetchMarketCandlesAsync(currency, options.timeframe, { force: Boolean(force) }).then(function (candles) {
                if (!candles || !candles.length || select.value !== currency.id) {
                    return;
                }

                updateTradeSummary(currency);
                drawAdvancedChart(element, currency, options);
            });
        }

        function updateTradeView(forceChartRefresh) {
            updateTradeSummary();
            renderTradeChart(forceChartRefresh);
        }

        select.addEventListener("change", function () {
            updateTradeView(true);
        });
        quantityInput.addEventListener("input", function () {
            updateTradeSummary(null, true);
        });

        [chartType, chartTimeframe, chartSma].forEach(function (control) {
            if (control) {
                control.addEventListener("change", function () {
                    renderTradeChart(true);
                });
            }
        });

        form.addEventListener("submit", function (event) {
            event.preventDefault();

            var submitter = event.submitter || document.activeElement;
            var side = submitter && submitter.name === "side" ? submitter.value : "buy";
            var result = performTrade(user.id, select.value, side, quantityInput.value);

            if (!result.ok) {
                showFlash(result.message, "error");
                return;
            }

            quantityInput.value = "";
            showFlash(result.message, "success");
            updateTradeView(true);
        });

        document.addEventListener("cryptotrade:prices-updated", function () {
            updateTradeView(true);
        });
        window.setInterval(function () {
            updateTradeView(true);
        }, CHART_REFRESH_INTERVAL_MS);
        updateTradeView(true);
    }

    function renderPortfolioPage(user) {
        var data = loadData();
        var portfolio = calculatePortfolio(user, data);
        var container = document.querySelector("[data-holdings]");
        var wallets = getUserWallets(data, user.id);

        setText("[data-portfolio-total]", formatMoney(portfolio.total));
        setText("[data-portfolio-crypto]", formatMoney(portfolio.crypto));
        setText("[data-portfolio-cash]", formatMoney(portfolio.cash));

        if (!container) {
            return;
        }

        if (!wallets.length) {
            container.innerHTML = '<div class="empty-state"><h2>Портфель пуст</h2><p class="muted">Купленные монеты появятся в этом разделе.</p></div>';
            return;
        }

        container.innerHTML = wallets.map(function (wallet) {
            var currency = getCurrency(data, wallet.currencyId);
            var value = currency ? roundMoney(wallet.amount * currency.price) : 0;
            var percent = portfolio.crypto ? Math.min(100, Math.round(value / portfolio.crypto * 100)) : 0;

            return [
                '<article class="holding-card">',
                '<div class="coin-cell">',
                currency ? currencyDot(currency) : "",
                '<div><strong>' + escapeHtml(currency ? currency.symbol : "N/A") + '</strong><small>' + escapeHtml(currency ? currency.name : "Актив") + '</small></div>',
                '</div>',
                '<strong>' + formatAmount(wallet.amount) + ' ' + escapeHtml(currency ? currency.symbol : "") + '</strong>',
                '<span class="muted">' + formatMoney(value) + '</span>',
                '<div class="bar"><span style="width: ' + percent + '%"></span></div>',
                '</article>'
            ].join("");
        }).join("");
    }

    function renderHistoryPage(user) {
        var table = document.querySelector("[data-history-table]");

        if (!table) {
            return;
        }

        var data = loadData();
        var transactions = data.transactions.filter(function (transaction) {
            return transaction.userId === user.id;
        }).slice().reverse();

        if (!transactions.length) {
            table.innerHTML = '<tr><td colspan="7" class="center muted">Операций пока нет.</td></tr>';
            return;
        }

        table.innerHTML = transactions.map(function (transaction) {
            var currency = getCurrency(data, transaction.currencyId);

            return [
                '<tr>',
                '<td>' + formatDate(transaction.createdAt) + '</td>',
                '<td><span class="side ' + (transaction.side === "buy" ? "buy" : "sell") + '">' + (transaction.side === "buy" ? "Покупка" : "Продажа") + '</span></td>',
                '<td>' + escapeHtml(currency ? currency.symbol : "") + '</td>',
                '<td>' + formatAmount(transaction.quantity) + '</td>',
                '<td>' + formatPrice(transaction.price) + '</td>',
                '<td>' + formatMoney(transaction.total) + '</td>',
                '<td>' + escapeHtml(transaction.status || "Исполнено") + '</td>',
                '</tr>'
            ].join("");
        }).join("");
    }

    function renderAdminCurrencyOptions(select, currencies) {
        if (!select) {
            return;
        }

        var currentValue = select.value;
        select.innerHTML = currencies.map(function (currency) {
            return '<option value="' + escapeHtml(currency.id) + '">' + escapeHtml(currency.symbol) + ' - ' + escapeHtml(currency.name) + '</option>';
        }).join("");

        if (currentValue && currencies.some(function (currency) { return currency.id === currentValue; })) {
            select.value = currentValue;
        }
    }

    function renderAdminTables() {
        var data = loadData();
        var users = loadUsers();
        var table = document.querySelector("[data-admin-currencies]");
        var transactionsTable = document.querySelector("[data-admin-transactions]");

        if (table) {
            table.innerHTML = data.currencies.map(function (currency) {
                return [
                    '<tr>',
                    '<td><strong>' + escapeHtml(currency.symbol) + '</strong></td>',
                    '<td>' + escapeHtml(currency.name) + '</td>',
                    '<td>' + formatPrice(currency.price) + '</td>',
                    '<td><span class="risk">' + escapeHtml(currency.risk) + '</span></td>',
                    '<td><span class="risk">' + escapeHtml(getPriceModeLabel(currency)) + '</span></td>',
                    '<td>' + escapeHtml(getPriceSourceLabel(currency)) + '</td>',
                    '<td><small>' + escapeHtml(getSyncStatusLabel(currency)) + '</small></td>',
                    '</tr>'
                ].join("");
            }).join("");
        }

        if (transactionsTable) {
            var transactions = data.transactions.slice().reverse();

            if (!transactions.length) {
                transactionsTable.innerHTML = '<tr><td colspan="7" class="center muted">Операций пользователей пока нет.</td></tr>';
            } else {
                transactionsTable.innerHTML = transactions.map(function (transaction) {
                    var currency = getCurrency(data, transaction.currencyId);
                    var user = users.find(function (candidate) {
                        return candidate.id === transaction.userId;
                    });
                    var userName = user ? user.name + " (" + user.email + ")" : "Пользователь удален";

                    if (transaction.isSimulated) {
                        userName += " / симуляция";
                    }

                    return [
                        '<tr>',
                        '<td>' + formatDate(transaction.createdAt) + '</td>',
                        '<td>' + escapeHtml(userName) + '</td>',
                        '<td><span class="side ' + (transaction.side === "buy" ? "buy" : "sell") + '">' + (transaction.side === "buy" ? "Покупка" : "Продажа") + '</span></td>',
                        '<td>' + escapeHtml(currency ? currency.symbol : "") + '</td>',
                        '<td>' + formatAmount(transaction.quantity) + '</td>',
                        '<td>' + formatPrice(transaction.price) + '</td>',
                        '<td>' + formatMoney(transaction.total) + '</td>',
                        '</tr>'
                    ].join("");
                }).join("");
            }
        }

        setText("[data-admin-users]", String(users.length));
        setText("[data-admin-transactions-count]", String(data.transactions.length));
        setText("[data-admin-turnover]", formatMoney(data.transactions.reduce(function (sum, transaction) {
            return sum + Number(transaction.total || 0);
        }, 0)));
        setText("[data-admin-simulation-state]", data.settings.simulationEnabled ? "Вкл." : "Выкл.");
        setText("[data-admin-simulation-summary]", users.filter(isSimulatedRecord).length + " пользователей, " + data.settings.simulationTradesPerMinute + " сделок/мин, " + data.transactions.filter(isSimulatedRecord).length + " операций");

        renderAdminCurrencyOptions(document.querySelector("[data-admin-price-currency]"), data.currencies);
        renderSimulationControls();
    }

    function renderSimulationControls() {
        var data = loadData();
        var settings = normalizeSettings(data.settings);
        var enabledInput = document.querySelector("[data-simulation-enabled]");
        var usersInput = document.querySelector("[data-simulation-users]");
        var tradesInput = document.querySelector("[data-simulation-trades]");
        var badge = document.querySelector("[data-simulation-badge]");

        if (enabledInput) {
            enabledInput.checked = settings.simulationEnabled;
        }

        if (usersInput) {
            usersInput.value = settings.simulationUsersTarget;
        }

        if (tradesInput) {
            tradesInput.value = settings.simulationTradesPerMinute;
        }

        if (badge) {
            badge.textContent = settings.simulationEnabled ? "Вкл." : "Выкл.";
        }
    }

    function initAdminPage() {
        var priceForm = document.querySelector("[data-admin-price-form]");
        var currencyForm = document.querySelector("[data-admin-currency-form]");
        var priceSelect = document.querySelector("[data-admin-price-currency]");
        var priceModeSelect = document.querySelector("[data-admin-price-mode]");
        var marketSymbolInput = document.querySelector("[data-admin-market-symbol]");
        var syncButton = document.querySelector("[data-admin-sync-prices]");
        var simulationForm = document.querySelector("[data-simulation-form]");
        var simulationGenerate = document.querySelector("[data-simulation-generate]");

        function updatePriceModeHint() {
            if (!priceModeSelect || !marketSymbolInput) {
                return;
            }

            marketSymbolInput.disabled = priceModeSelect.value !== PRICE_MODE_AUTO;
        }

        function syncPriceInput() {
            var data = loadData();
            var currency = getCurrency(data, priceSelect ? priceSelect.value : "");
            var priceInput = priceForm ? priceForm.elements.price : null;

            if (currency && priceInput) {
                priceInput.value = currency.price;
            }

            if (currency && priceModeSelect) {
                priceModeSelect.value = currency.priceMode;
            }

            if (currency && marketSymbolInput) {
                marketSymbolInput.value = currency.marketSymbol || "";
            }

            updatePriceModeHint();
        }

        renderAdminTables();
        syncPriceInput();

        if (priceSelect) {
            priceSelect.addEventListener("change", syncPriceInput);
        }

        if (priceModeSelect) {
            priceModeSelect.addEventListener("change", updatePriceModeHint);
        }

        if (priceForm) {
            priceForm.addEventListener("submit", function (event) {
                event.preventDefault();

                var result = updateCurrencyPrice(
                    priceForm.elements.currency_id.value,
                    priceForm.elements.price.value,
                    priceForm.elements.price_mode.value,
                    priceForm.elements.market_symbol.value
                );

                showFlash(result.message, result.ok ? "success" : "error");
                renderAdminTables();
                syncPriceInput();
            });
        }

        if (syncButton) {
            syncButton.addEventListener("click", function () {
                syncButton.disabled = true;
                syncButton.textContent = "Обновление...";

                syncMarketPrices({ force: true }).then(function (result) {
                    showFlash(result.message, result.ok ? "success" : "error");
                    renderAdminTables();
                    syncPriceInput();
                    notifyPricesUpdated();
                    syncButton.disabled = false;
                    syncButton.textContent = "Обновить авто-курсы";
                });
            });
        }

        if (simulationForm) {
            simulationForm.addEventListener("submit", function (event) {
                event.preventDefault();

                var result = updateSimulationSettings(
                    simulationForm.elements.enabled.checked,
                    {
                        usersCount: simulationForm.elements.users_count.value,
                        tradesPerMinute: simulationForm.elements.trades_per_minute.value
                    }
                );

                showFlash(result.message, result.ok ? "success" : "error");
                renderAdminTables();
                notifySimulationUpdated();
            });
        }

        if (simulationGenerate) {
            simulationGenerate.addEventListener("click", function () {
                var result = runSimulationTick(true);

                showFlash(result.message, result.ok ? "success" : "error");
                renderAdminTables();
                notifySimulationUpdated();
            });
        }

        if (currencyForm) {
            currencyForm.addEventListener("submit", function (event) {
                event.preventDefault();

                var result = addCurrency(
                    currencyForm.elements.symbol.value,
                    currencyForm.elements.name.value,
                    currencyForm.elements.price.value,
                    currencyForm.elements.risk.value,
                    currencyForm.elements.description.value,
                    currencyForm.elements.price_mode.value,
                    currencyForm.elements.market_symbol.value
                );

                showFlash(result.message, result.ok ? "success" : "error");

                if (result.ok) {
                    currencyForm.reset();
                }

                renderAdminTables();
                syncPriceInput();
            });
        }

        document.addEventListener("cryptotrade:prices-updated", function () {
            renderAdminTables();
            syncPriceInput();
        });
    }

    function drawCurrencyCharts() {
        var data = loadData();

        document.querySelectorAll("[data-chart-currency]").forEach(function (canvas) {
            drawChart(canvas, getCurrency(data, canvas.dataset.chartCurrency), {
                timeframe: canvas.dataset.chartTimeframe || "5"
            });
        });
    }

    function getChartThemeColor(name, fallback) {
        if (!window.getComputedStyle) {
            return fallback;
        }

        return window.getComputedStyle(document.body).getPropertyValue(name).trim() || fallback;
    }

    function candleCacheKey(currency, timeframe) {
        return normalizeMarketSymbol(currency && (currency.marketSymbol || currency.symbol + "USDT")) + ":" + intervalForTimeframe(timeframe);
    }

    function normalizeMarketCandles(payload) {
        return payload.map(function (item) {
            return {
                time: Number(item.time),
                open: roundPrice(item.open),
                high: roundPrice(item.high),
                low: roundPrice(item.low),
                close: roundPrice(item.close),
                volume: Number(item.volume) || 0,
                source: item.source || "market"
            };
        }).filter(function (item) {
            return item.time && item.open && item.high && item.low && item.close;
        });
    }

    function applyMarketCandlesToCurrency(currency, candles, persist) {
        var latest = candles && candles.length ? candles[candles.length - 1] : null;
        var data;
        var stored;

        if (!currency || !latest || !latest.close) {
            return;
        }

        currency.price = latest.close;
        currency.lastSyncAt = new Date(latest.time * 1000).toISOString();
        currency.lastSyncStatus = "ok";
        currency.lastSyncMessage = "Рыночные свечи " + (latest.source || "биржи");
        currency.history = candles.slice(-30).map(function (item) {
            return item.close;
        });

        if (!persist) {
            return;
        }

        data = loadData();
        stored = getCurrency(data, currency.id);

        if (!stored) {
            return;
        }

        stored.price = currency.price;
        stored.lastSyncAt = currency.lastSyncAt;
        stored.lastSyncStatus = currency.lastSyncStatus;
        stored.lastSyncMessage = currency.lastSyncMessage;
        stored.history = currency.history.slice();
        saveData(data);
    }

    function getCachedMarketCandles(currency, timeframe) {
        var cached = marketCandleCache[candleCacheKey(currency, timeframe)];

        if (!cached || !Array.isArray(cached.candles) || !cached.candles.length) {
            return null;
        }

        return cached.candles;
    }

    function fetchMarketCandlesAsync(currency, timeframe, options) {
        var symbol = normalizeMarketSymbol(currency.marketSymbol || currency.symbol + "USDT");
        var interval = intervalForTimeframe(timeframe);
        var key = candleCacheKey(currency, timeframe);
        var cached = marketCandleCache[key];
        var force = options && options.force;
        var persist = options && options.persist;

        if (!symbol || !canUseBackendApi()) {
            return Promise.resolve(null);
        }

        if (!force && cached && cached.candles && Date.now() - cached.loadedAt < MARKET_CANDLE_CACHE_MS) {
            return Promise.resolve(cached.candles);
        }

        if (!force && cached && cached.pending) {
            return cached.pending;
        }

        marketCandleCache[key] = cached || {};
        marketCandleCache[key].pending = apiFetchJson("/api/klines?symbol=" + encodeURIComponent(symbol) + "&interval=" + encodeURIComponent(interval) + "&limit=" + MARKET_CANDLE_LIMIT).then(function (response) {
            var candles = response && response.ok && Array.isArray(response.candles)
                ? normalizeMarketCandles(response.candles)
                : null;

            if (candles && candles.length) {
                marketCandleCache[key] = {
                    candles: candles,
                    loadedAt: Date.now()
                };
                applyMarketCandlesToCurrency(currency, candles, persist);
                return candles;
            }

            if (marketCandleCache[key]) {
                marketCandleCache[key].pending = null;
            }

            return null;
        });

        return marketCandleCache[key].pending;
    }

    function buildCandles(currency, timeframe) {
        var marketCandles = getCachedMarketCandles(currency, timeframe);

        if (marketCandles) {
            return marketCandles;
        }

        var history = Array.isArray(currency.history) && currency.history.length ? currency.history : [currency.price];
        var intervalMinutes = Number(timeframe || 1) || 1;
        var synthetic = history.slice();

        while (synthetic.length < 80) {
            synthetic.unshift(roundPrice(synthetic[0] * (0.998 + (synthetic.length % 5) * 0.0008)));
        }

        var startTime = Math.floor(Date.now() / 1000) - synthetic.length * intervalMinutes * 60;
        var raw = synthetic.map(function (close, index) {
            var previous = index ? Number(synthetic[index - 1]) || close : close * 0.995;
            var high = Math.max(previous, close) * (1 + 0.003 + (index % 3) * 0.001);
            var low = Math.min(previous, close) * (1 - 0.003 - (index % 2) * 0.001);

            return {
                time: startTime + index * intervalMinutes * 60,
                open: roundPrice(previous),
                high: roundPrice(high),
                low: roundPrice(low),
                close: roundPrice(close),
                source: "local"
            };
        });

        return raw.slice(-120);
    }

    function calculateSma(values, period) {
        return values.map(function (value, index) {
            var start = Math.max(0, index - period + 1);
            var slice = values.slice(start, index + 1);
            return slice.reduce(function (sum, item) {
                return sum + item;
            }, 0) / slice.length;
        });
    }

    function renderChartAnalysis(currency, candles, timeframe) {
        var holder = document.querySelector("[data-chart-analysis]");

        if (!holder || !candles.length) {
            return;
        }

        var first = candles[0].close;
        var last = candles[candles.length - 1].close;
        var highs = candles.map(function (item) { return item.high; });
        var lows = candles.map(function (item) { return item.low; });
        var trend = first ? ((last - first) / first) * 100 : 0;
        var volatility = last ? ((Math.max.apply(null, highs) - Math.min.apply(null, lows)) / last) * 100 : 0;
        var sma = calculateSma(candles.map(function (item) { return item.close; }), 5).pop();
        var signal = last >= sma ? "выше SMA(5)" : "ниже SMA(5)";
        var timeframeLabel = String(timeframe) === "60" ? "1ч" : String(timeframe) + "м";
        var sourceLabel = candles[0] && candles[0].source && candles[0].source !== "local" ? candles[0].source + " candles" : "локальная история";

        holder.innerHTML = [
            '<span>Таймфрейм: ' + escapeHtml(timeframeLabel) + '</span>',
            '<span>Источник: ' + escapeHtml(sourceLabel) + '</span>',
            '<span>Тренд: <strong class="trend ' + (trend >= 0 ? "up" : "down") + '">' + formatPercent(trend) + '</strong></span>',
            '<span>Волатильность: ' + volatility.toFixed(2) + '%</span>',
            '<span>Цена ' + signal + '</span>',
            '<span>Последняя: ' + formatPrice(currency.price) + '</span>'
        ].join("");
    }

    function drawTradingViewChart(container, currency, candles, options) {
        var chartApi = window.LightweightCharts;
        var rect = container.getBoundingClientRect ? container.getBoundingClientRect() : { width: 620, height: 390 };
        var width = Math.max(320, Math.round(rect.width || container.clientWidth || 620));
        var height = Math.max(300, Math.round(rect.height || container.clientHeight || 390));
        var ink = getChartThemeColor("--ink", "#171a16");
        var muted = getChartThemeColor("--muted", "#667064");
        var surface = getChartThemeColor("--surface", "#ffffff");
        var line = getChartThemeColor("--line", "#dce3d7");
        var success = getChartThemeColor("--success-ink", "#08734e");
        var danger = getChartThemeColor("--danger-ink", "#a7322b");
        var candleData = candles.map(function (item, index) {
            return {
                time: Number(item.time) || Math.floor(Date.now() / 1000) - (candles.length - index) * (Number(options.timeframe || 1) * 60),
                open: item.open,
                high: item.high,
                low: item.low,
                close: item.close
            };
        });
        var chart;
        var mainSeries;
        var smaSeries;

        container.innerHTML = "";
        container.classList.remove("is-hidden");

        chart = chartApi.createChart(container, {
            width: width,
            height: height,
            layout: {
                background: { type: "solid", color: surface },
                textColor: muted
            },
            attributionLogo: true,
            grid: {
                vertLines: { color: line },
                horzLines: { color: line }
            },
            rightPriceScale: {
                borderColor: line
            },
            timeScale: {
                borderColor: line,
                timeVisible: true,
                secondsVisible: false
            },
            crosshair: {
                mode: 1
            }
        });

        function addLineSeries(chartInstance, settings) {
            if (chartInstance.addSeries && chartApi.LineSeries) {
                return chartInstance.addSeries(chartApi.LineSeries, settings);
            }

            return chartInstance.addLineSeries(settings);
        }

        function addCandleSeries(chartInstance, settings) {
            if (chartInstance.addSeries && chartApi.CandlestickSeries) {
                return chartInstance.addSeries(chartApi.CandlestickSeries, settings);
            }

            return chartInstance.addCandlestickSeries(settings);
        }

        if (options.type === "line") {
            mainSeries = addLineSeries(chart, {
                color: safeColor(currency.color),
                lineWidth: 3
            });
            mainSeries.setData(candleData.map(function (item) {
                return {
                    time: item.time,
                    value: item.close
                };
            }));
        } else {
            mainSeries = addCandleSeries(chart, {
                upColor: success,
                downColor: danger,
                borderUpColor: success,
                borderDownColor: danger,
                wickUpColor: success,
                wickDownColor: danger
            });
            mainSeries.setData(candleData);
        }

        if (options.showSma) {
            smaSeries = addLineSeries(chart, {
                color: getChartThemeColor("--accent-2", "#f2b705"),
                lineWidth: 2,
                priceLineVisible: false
            });
            smaSeries.setData(calculateSma(candles.map(function (item) {
                return item.close;
            }), 5).map(function (value, index) {
                return {
                    time: candleData[index].time,
                    value: value
                };
            }));
        }

        chart.timeScale().fitContent();
        window.setTimeout(function () {
            chart.resize(Math.max(320, container.clientWidth || width), height);
            chart.timeScale().fitContent();
        }, 0);

        return chart;
    }

    function drawAdvancedChart(element, currency, options) {
        var canvas;
        var candles;

        if (!element || !currency) {
            return;
        }

        candles = buildCandles(currency, options && options.timeframe);

        if (element.dataset && Object.prototype.hasOwnProperty.call(element.dataset, "tvChart") && window.LightweightCharts) {
            canvas = document.querySelector("[data-advanced-chart]");

            if (canvas) {
                canvas.classList.add("is-hidden");
            }

            drawTradingViewChart(element, currency, candles, options || {});
            renderChartAnalysis(currency, candles, options && options.timeframe || "1");
            return;
        }

        canvas = element.dataset && Object.prototype.hasOwnProperty.call(element.dataset, "tvChart")
            ? document.querySelector("[data-advanced-chart]")
            : element;

        if (!canvas || !currency || !canvas.getContext) {
            return;
        }

        var closes = candles.map(function (item) { return item.close; });
        var allValues = [];
        var rect = canvas.getBoundingClientRect ? canvas.getBoundingClientRect() : { width: 620, height: 390 };
        var width = Math.max(320, Math.round(rect.width || canvas.clientWidth || 620));
        var height = Math.max(260, Math.round(rect.height || canvas.clientHeight || 390));
        var ratio = window.devicePixelRatio || 1;
        var paddingLeft = 48;
        var paddingRight = 18;
        var paddingTop = 22;
        var paddingBottom = 34;
        var chartWidth = width - paddingLeft - paddingRight;
        var chartHeight = height - paddingTop - paddingBottom;
        var ctx = canvas.getContext("2d");
        var ink = getChartThemeColor("--ink", "#171a16");
        var muted = getChartThemeColor("--muted", "#667064");
        var line = getChartThemeColor("--line", "#dce3d7");
        var accent = safeColor(currency.color);
        var success = getChartThemeColor("--success-ink", "#08734e");
        var danger = getChartThemeColor("--danger-ink", "#a7322b");
        var min;
        var max;
        var range;

        if (element.dataset && Object.prototype.hasOwnProperty.call(element.dataset, "tvChart")) {
            element.classList.add("is-hidden");
            canvas.classList.remove("is-hidden");
        }

        candles.forEach(function (item) {
            allValues.push(item.high, item.low);
        });

        min = Math.min.apply(null, allValues);
        max = Math.max.apply(null, allValues);
        range = max - min || 1;

        function xAt(index) {
            return paddingLeft + (candles.length === 1 ? chartWidth / 2 : index / (candles.length - 1) * chartWidth);
        }

        function yAt(value) {
            return paddingTop + (max - value) / range * chartHeight;
        }

        canvas.width = width * ratio;
        canvas.height = height * ratio;
        canvas.style.width = width + "px";
        canvas.style.height = height + "px";
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        ctx.clearRect(0, 0, width, height);

        ctx.strokeStyle = line;
        ctx.lineWidth = 1;
        ctx.fillStyle = muted;
        ctx.font = "12px Segoe UI, Arial, sans-serif";

        [0, 0.25, 0.5, 0.75, 1].forEach(function (step) {
            var y = paddingTop + chartHeight * step;
            var value = max - range * step;
            ctx.beginPath();
            ctx.moveTo(paddingLeft, y);
            ctx.lineTo(width - paddingRight, y);
            ctx.stroke();
            ctx.fillText(formatPrice(value), 6, y + 4);
        });

        if (options && options.type === "line") {
            ctx.strokeStyle = accent;
            ctx.lineWidth = 3;
            ctx.lineJoin = "round";
            ctx.lineCap = "round";
            ctx.beginPath();
            closes.forEach(function (close, index) {
                var x = xAt(index);
                var y = yAt(close);

                if (!index) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            ctx.stroke();
        } else {
            var candleWidth = Math.max(5, Math.min(18, chartWidth / candles.length * 0.58));

            candles.forEach(function (item, index) {
                var x = xAt(index);
                var isUp = item.close >= item.open;
                var top = yAt(Math.max(item.open, item.close));
                var bottom = yAt(Math.min(item.open, item.close));

                ctx.strokeStyle = isUp ? success : danger;
                ctx.fillStyle = isUp ? success : danger;
                ctx.beginPath();
                ctx.moveTo(x, yAt(item.high));
                ctx.lineTo(x, yAt(item.low));
                ctx.stroke();
                ctx.fillRect(x - candleWidth / 2, top, candleWidth, Math.max(2, bottom - top));
            });
        }

        if (!options || options.showSma) {
            var smaValues = calculateSma(closes, 5);

            ctx.strokeStyle = getChartThemeColor("--accent-2", "#f2b705");
            ctx.lineWidth = 2;
            ctx.beginPath();
            smaValues.forEach(function (value, index) {
                var x = xAt(index);
                var y = yAt(value);

                if (!index) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            });
            ctx.stroke();
        }

        ctx.fillStyle = ink;
        ctx.font = "700 13px Segoe UI, Arial, sans-serif";
        ctx.fillText(currency.symbol + " / USD", paddingLeft, 16);
        ctx.fillStyle = muted;
        ctx.font = "12px Segoe UI, Arial, sans-serif";
        ctx.fillText("SMA(5)", width - 72, 16);

        renderChartAnalysis(currency, candles, options && options.timeframe || "1");
    }

    function drawChart(canvas, currency, options) {
        if (!canvas || !currency || !canvas.getContext) {
            return;
        }

        var timeframe = options && options.timeframe || "5";
        var candles = buildCandles(currency, timeframe);
        var history = candles.length
            ? candles.map(function (item) { return item.close; })
            : (Array.isArray(currency.history) && currency.history.length ? currency.history : [currency.price]);
        var rect = canvas.getBoundingClientRect ? canvas.getBoundingClientRect() : { width: 360, height: 180 };
        var computed = window.getComputedStyle ? window.getComputedStyle(canvas) : null;
        var width = Math.max(220, Math.round(rect.width || canvas.clientWidth || 360));
        var height = Math.max(54, Math.round(rect.height || parseInt(computed && computed.height, 10) || canvas.clientHeight || 180));
        var ratio = window.devicePixelRatio || 1;
        var min = Math.min.apply(null, history);
        var max = Math.max.apply(null, history);
        var range = max - min || 1;
        var padding = height < 80 ? 8 : 18;
        var ctx = canvas.getContext("2d");

        canvas.width = width * ratio;
        canvas.height = height * ratio;
        canvas.style.width = width + "px";
        canvas.style.height = height + "px";
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        ctx.clearRect(0, 0, width, height);

        ctx.strokeStyle = "rgba(102, 112, 100, 0.25)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, height - padding);
        ctx.lineTo(width, height - padding);
        ctx.stroke();

        ctx.strokeStyle = safeColor(currency.color);
        ctx.lineWidth = height < 80 ? 2 : 3;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        ctx.beginPath();

        history.forEach(function (value, index) {
            var x = history.length === 1 ? width / 2 : index / (history.length - 1) * (width - padding * 2) + padding;
            var y = height - padding - ((value - min) / range) * (height - padding * 2);

            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });

        ctx.stroke();

        if (!options || !options.skipFetch) {
            fetchMarketCandlesAsync(currency, timeframe, { force: Boolean(options && options.force) }).then(function (loadedCandles) {
                if (!loadedCandles || !loadedCandles.length || !canvas.isConnected) {
                    return;
                }

                drawChart(canvas, currency, {
                    timeframe: timeframe,
                    skipFetch: true
                });
            });
        }
    }

    function renderPage(page, user) {
        renderMarketCards("[data-auth-market]", 4);

        if (!user) {
            return;
        }

        if (page === "dashboard") {
            renderDashboardPage(user);
        }

        if (page === "market") {
            renderMarketTable();
        }

        if (page === "trade") {
            initTradePage(user);
        }

        if (page === "portfolio") {
            renderPortfolioPage(user);
        }

        if (page === "history") {
            renderHistoryPage(user);
        }

        if (page === "admin") {
            initAdminPage();
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var page = document.body.dataset.page;

        loadUsers();
        loadData();
        initThemeToggle();
        initAuthSwitcher();
        initLoginForm();
        initRegisterForm();
        renderMarketCards("[data-auth-market]", 4);
        renderPage(page, initSessionUi());
        initPriceAutoRefresh(page);
        initSimulationAutoRefresh(page);
    });

    window.CryptoTradeApp = {
        addCurrency: addCurrency,
        authenticate: authenticate,
        calculatePortfolio: calculatePortfolio,
        clearSession: clearSession,
        loadData: loadData,
        loadUsers: loadUsers,
        performTrade: performTrade,
        registerUser: registerUser,
        runSimulationTick: runSimulationTick,
        syncMarketPrices: syncMarketPrices,
        updateSimulationSettings: updateSimulationSettings,
        updateCurrencyPrice: updateCurrencyPrice
    };
}());
