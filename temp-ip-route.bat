@echo off
chcp 65001 > nul

:: Имя VPN интерфейса
set "INTERFACE_NAME=VPN - VPN Client"
:: Шлюз VPN интерфейса
set "INTERFACE_GATEWAY=10.211.254.254"

:: Выключаем и включаем интерфейс для сброса маршрутов и возможности установить новую метрику
netsh interface set interface "%INTERFACE_NAME%" admin=disabled
:: timeout /t 1 /nobreak >nul
netsh interface set interface "%INTERFACE_NAME%" admin=enabled
:: timeout /t 1 /nobreak >nul

echo Понижаем метрику VPN интерфейса
netsh interface ipv4 set interface "%INTERFACE_NAME%" metric=100

echo Выясняем номер интерфейса для добавления маршрутов
for /F "skip=3 tokens=1,2,3,4,* delims= " %%G in ('netsh interface ipv4 show interface') DO (
    if "%%K"=="%INTERFACE_NAME%" (
        echo Номер интерфейса "%INTERFACE_NAME%": %%G
        set INTERFACE_INDEX=%%G 
    )
)

:: Удаляем маршрут по умолчанию для VPN
:: route delete 0.0.0.0 %INTERFACE_GATEWAY%

route add 1.1.1.1 mask 255.255.255.255 %INTERFACE_GATEWAY% if %INTERFACE_INDEX%

cls
echo Чтобы закрыть скрипт и восстановить метрику интерфейса по умолчанию и удалить добавленные маршруты
pause
netsh interface ipv4 set interface "%INTERFACE_NAME%" metric=1
netsh interface set interface "%INTERFACE_NAME%" admin=disabled
:: timeout /t 1 /nobreak >nul
netsh interface set interface "%INTERFACE_NAME%" admin=enabled

