#!/bin/bash
# Script de Instalação do TigerOne no Ubuntu

set -e

echo "=== 0. Configurando fuso horário para São Paulo ==="
sudo timedatectl set-timezone America/Sao_Paulo

echo "=== 1. Atualizando pacotes do sistema ==="
sudo apt update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade
sudo apt install -y git python3-pip python3-venv python3-full curl build-essential

echo "=== 2. Clonando o repositório TigerOne ==="
cd /root
if [ -d "TigerOne" ]; then
    echo "Pasta TigerOne já existe. Atualizando código..."
    cd TigerOne
    git pull
else
    git clone git@github.com:ricardohabueno/TigerOne.git
    cd TigerOne
fi

echo "=== 3. Criando Ambiente Virtual (venv) ==="
python3 -m venv venv
source venv/bin/activate

echo "=== 4. Instalando dependências do Python ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 5. Instalando o Playwright e o Chromium ==="
playwright install --with-deps chromium

echo "=== 6. Configurando o serviço do sistema (systemd) ==="
sudo bash -c 'cat > /etc/systemd/system/tigerone.service <<EOF
[Unit]
Description=TigerOne Campanhas Inteligentes API
After=network.target

[Service]
User=root
WorkingDirectory=/root/TigerOne
Environment="TZ=America/Sao_Paulo"
ExecStart=/root/TigerOne/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF'

echo "=== 7. Iniciando e ativando o serviço ==="
sudo systemctl daemon-reload
sudo systemctl enable tigerone
sudo systemctl start tigerone

echo "=== Instalação Concluída com Sucesso! ==="
echo "O TigerOne está online. Acesse no navegador: http://161.35.102.109:8000"
