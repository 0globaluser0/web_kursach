# Схема данных CryptoTrade

В проекте используется логическая модель из шести основных связанных сущностей и одной служебной сущности настроек. В программной части данные сохраняются в SQLite-базе `site/cryptotrade.db`, а сайт обращается к ней через Python API в файле `site/backend.py`.

## Сущности

| Сущность | Поля | Назначение |
| --- | --- | --- |
| `roles` | `id`, `code`, `title` | Роли пользователей: трейдер, администратор и симулянт |
| `users` | `id`, `role_id`, `name`, `email`, `password`, `balance_usd`, `created_at`, `is_simulated` | Пользователи сайта, учетные данные, учебный USD-баланс и признак симуляции |
| `currencies` | `id`, `symbol`, `name`, `price`, `color`, `risk`, `description`, `price_mode`, `market_symbol`, `source`, `last_sync_at`, `last_sync_status`, `last_sync_message` | Криптовалюты, текущие цены, описание, уровень риска и источник обновления курса |
| `wallets` | `id`, `user_id`, `currency_id`, `amount`, `updated_at`, `is_simulated` | Балансы пользователей по криптовалютам |
| `transactions` | `id`, `user_id`, `currency_id`, `side`, `quantity`, `price`, `total`, `status`, `created_at`, `is_simulated` | Завершенные операции пользователей |
| `price_history` | `id`, `currency_id`, `price`, `recorded_at`, `position` | История изменения курсов активов |
| `system_settings` | `id`, `simulation_enabled`, `simulation_level`, `simulation_users_target`, `simulation_trades_per_minute`, `last_simulation_at`, `simulation_carry` | Служебные настройки режима симуляции активности |

В JavaScript-коде часть полей записана в стиле camelCase: `balance_usd` соответствует `balanceUsd`, `user_id` соответствует `userId`, `currency_id` соответствует `currencyId`, `created_at` соответствует `createdAt`, `price_mode` соответствует `priceMode`, `market_symbol` соответствует `marketSymbol`, `last_sync_at` соответствует `lastSyncAt`, `last_sync_status` соответствует `lastSyncStatus`, `last_sync_message` соответствует `lastSyncMessage`, `is_simulated` соответствует `isSimulated`. История цен возвращается интерфейсу как массив `history`, но физически хранится в таблице `price_history`.

## Связи

- `users.role_id` -> `roles.id`
- `wallets.user_id` -> `users.id`
- `wallets.currency_id` -> `currencies.id`
- `transactions.user_id` -> `users.id`
- `transactions.currency_id` -> `currencies.id`
- `price_history.currency_id` -> `currencies.id`
- `system_settings.id = 'main'` -> одна служебная запись настроек

## Хранение в SQLite

Физическая база данных создается автоматически при запуске:

```text
site/cryptotrade.db
```

В SQLite создаются таблицы `roles`, `users`, `currencies`, `wallets`, `transactions`, `price_history`, `system_settings`. Между таблицами заданы внешние ключи, поэтому кошельки, транзакции и история цен связаны с пользователями и активами. Симулируемые пользователи получают роль `simulator`, что позволяет отличать их от реальных трейдеров.

`localStorage` больше не используется как база данных. В нем остаются только локальные настройки браузера: выбранная тема, текущая сессия и служебная информация о последнем запросе курса.

Отдельная таблица `orders` не используется. В учебной модели сделка исполняется сразу после проверки баланса или количества монет, поэтому результат сохраняется непосредственно в таблицу `transactions`.
