#!/bin/bash

# EasySight 分布式Worker节点部署脚本
# 使用方法: ./deploy_worker.sh [选项]

set -e

# 默认配置
DEFAULT_MASTER_HOST="localhost"
DEFAULT_MASTER_PORT="8000"
DEFAULT_WORKER_NAME="worker-$(hostname)"
DEFAULT_POOL_SIZE="3"
DEFAULT_INSTALL_DIR="/opt/easysight"
DEFAULT_USER="easysight"
DEFAULT_LOG_DIR="/var/log/easysight"
DEFAULT_CONFIG_DIR="/etc/easysight"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
EasySight 分布式Worker节点部署脚本

使用方法:
    $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -m, --master-host       主节点地址 (默认: $DEFAULT_MASTER_HOST)
    -p, --master-port       主节点端口 (默认: $DEFAULT_MASTER_PORT)
    -n, --worker-name       Worker节点名称 (默认: $DEFAULT_WORKER_NAME)
    -s, --pool-size         Worker池大小 (默认: $DEFAULT_POOL_SIZE)
    -d, --install-dir       安装目录 (默认: $DEFAULT_INSTALL_DIR)
    -u, --user              运行用户 (默认: $DEFAULT_USER)
    -l, --log-dir           日志目录 (默认: $DEFAULT_LOG_DIR)
    -c, --config-dir        配置目录 (默认: $DEFAULT_CONFIG_DIR)
    --docker                使用Docker部署
    --systemd               安装systemd服务
    --uninstall             卸载Worker节点
    --dry-run               仅显示将要执行的操作，不实际执行

示例:
    # 基本部署
    $0 --master-host 192.168.1.100 --worker-name worker-1
    
    # Docker部署
    $0 --docker --master-host 192.168.1.100
    
    # 安装systemd服务
    $0 --systemd --master-host 192.168.1.100
    
    # 卸载
    $0 --uninstall

EOF
}

# 解析命令行参数
parse_args() {
    MASTER_HOST="$DEFAULT_MASTER_HOST"
    MASTER_PORT="$DEFAULT_MASTER_PORT"
    WORKER_NAME="$DEFAULT_WORKER_NAME"
    POOL_SIZE="$DEFAULT_POOL_SIZE"
    INSTALL_DIR="$DEFAULT_INSTALL_DIR"
    USER="$DEFAULT_USER"
    LOG_DIR="$DEFAULT_LOG_DIR"
    CONFIG_DIR="$DEFAULT_CONFIG_DIR"
    USE_DOCKER=false
    INSTALL_SYSTEMD=false
    UNINSTALL=false
    DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -m|--master-host)
                MASTER_HOST="$2"
                shift 2
                ;;
            -p|--master-port)
                MASTER_PORT="$2"
                shift 2
                ;;
            -n|--worker-name)
                WORKER_NAME="$2"
                shift 2
                ;;
            -s|--pool-size)
                POOL_SIZE="$2"
                shift 2
                ;;
            -d|--install-dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -u|--user)
                USER="$2"
                shift 2
                ;;
            -l|--log-dir)
                LOG_DIR="$2"
                shift 2
                ;;
            -c|--config-dir)
                CONFIG_DIR="$2"
                shift 2
                ;;
            --docker)
                USE_DOCKER=true
                shift
                ;;
            --systemd)
                INSTALL_SYSTEMD=true
                shift
                ;;
            --uninstall)
                UNINSTALL=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 执行命令（支持dry-run）
execute_cmd() {
    local cmd="$1"
    local description="$2"
    
    if [[ "$description" != "" ]]; then
        log_info "$description"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "[DRY-RUN] $cmd"
    else
        eval "$cmd"
    fi
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "此脚本仅支持Linux系统"
        exit 1
    fi
    
    # 检查权限
    if [[ $EUID -ne 0 ]] && [[ "$USE_DOCKER" == "false" ]]; then
        log_error "需要root权限来安装系统服务"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python 3"
        exit 1
    fi
    
    # 检查Docker（如果使用Docker部署）
    if [[ "$USE_DOCKER" == "true" ]] && ! command -v docker &> /dev/null; then
        log_error "未找到Docker"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 创建用户和目录
setup_user_and_dirs() {
    log_info "设置用户和目录..."
    
    # 创建用户
    if ! id "$USER" &>/dev/null; then
        execute_cmd "useradd -r -s /bin/false -d $INSTALL_DIR $USER" "创建用户 $USER"
    fi
    
    # 创建目录
    execute_cmd "mkdir -p $INSTALL_DIR" "创建安装目录"
    execute_cmd "mkdir -p $LOG_DIR" "创建日志目录"
    execute_cmd "mkdir -p $CONFIG_DIR" "创建配置目录"
    
    # 设置权限
    execute_cmd "chown -R $USER:$USER $INSTALL_DIR" "设置安装目录权限"
    execute_cmd "chown -R $USER:$USER $LOG_DIR" "设置日志目录权限"
    execute_cmd "chmod 755 $CONFIG_DIR" "设置配置目录权限"
}

# 安装Python依赖
install_dependencies() {
    log_info "安装Python依赖..."
    
    # 创建虚拟环境
    execute_cmd "python3 -m venv $INSTALL_DIR/venv" "创建Python虚拟环境"
    
    # 安装依赖
    execute_cmd "$INSTALL_DIR/venv/bin/pip install --upgrade pip" "升级pip"
    
    if [[ -f "requirements.txt" ]]; then
        execute_cmd "$INSTALL_DIR/venv/bin/pip install -r requirements.txt" "安装Python依赖"
    else
        log_warning "未找到requirements.txt文件"
    fi
}

# 复制应用文件
copy_application() {
    log_info "复制应用文件..."
    
    # 复制源代码
    execute_cmd "cp -r . $INSTALL_DIR/" "复制应用代码"
    
    # 设置权限
    execute_cmd "chown -R $USER:$USER $INSTALL_DIR" "设置文件权限"
    execute_cmd "chmod +x $INSTALL_DIR/start_worker.py" "设置执行权限"
}

# 创建配置文件
create_config() {
    log_info "创建配置文件..."
    
    local config_file="$CONFIG_DIR/worker.env"
    
    execute_cmd "cat > $config_file << EOF
# EasySight Worker节点配置
WORKER_NODE_NAME=$WORKER_NAME
WORKER_WORKER_POOL_SIZE=$POOL_SIZE
WORKER_MASTER_HOST=$MASTER_HOST
WORKER_MASTER_PORT=$MASTER_PORT
WORKER_LOG_LEVEL=INFO
WORKER_LOG_FILE=$LOG_DIR/worker.log
WORKER_HEARTBEAT_INTERVAL=30
WORKER_TASK_POLL_INTERVAL=5
EOF" "创建配置文件"
    
    execute_cmd "chmod 644 $config_file" "设置配置文件权限"
}

# 安装systemd服务
install_systemd_service() {
    log_info "安装systemd服务..."
    
    local service_file="/etc/systemd/system/easysight-worker.service"
    
    execute_cmd "cat > $service_file << EOF
[Unit]
Description=EasySight Distributed Worker Node
After=network.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
EnvironmentFile=$CONFIG_DIR/worker.env
ExecStart=$INSTALL_DIR/venv/bin/python start_worker.py --config $CONFIG_DIR/worker.env
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=30

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=easysight-worker

# 安全配置
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$LOG_DIR $INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOF" "创建systemd服务文件"
    
    execute_cmd "systemctl daemon-reload" "重新加载systemd配置"
    execute_cmd "systemctl enable easysight-worker" "启用服务"
}

# Docker部署
docker_deploy() {
    log_info "使用Docker部署Worker节点..."
    
    # 构建镜像
    execute_cmd "docker build -f Dockerfile.worker -t easysight-worker ." "构建Docker镜像"
    
    # 运行容器
    execute_cmd "docker run -d \
        --name easysight-worker-$WORKER_NAME \
        --restart unless-stopped \
        -e WORKER_MASTER_HOST=$MASTER_HOST \
        -e WORKER_MASTER_PORT=$MASTER_PORT \
        -e WORKER_NODE_NAME=$WORKER_NAME \
        -e WORKER_WORKER_POOL_SIZE=$POOL_SIZE \
        -v $LOG_DIR:/app/logs \
        easysight-worker" "启动Docker容器"
}

# 卸载Worker节点
uninstall_worker() {
    log_info "卸载EasySight Worker节点..."
    
    # 停止服务
    if systemctl is-active --quiet easysight-worker; then
        execute_cmd "systemctl stop easysight-worker" "停止服务"
    fi
    
    if systemctl is-enabled --quiet easysight-worker; then
        execute_cmd "systemctl disable easysight-worker" "禁用服务"
    fi
    
    # 删除服务文件
    if [[ -f "/etc/systemd/system/easysight-worker.service" ]]; then
        execute_cmd "rm /etc/systemd/system/easysight-worker.service" "删除服务文件"
        execute_cmd "systemctl daemon-reload" "重新加载systemd配置"
    fi
    
    # 停止Docker容器
    if command -v docker &> /dev/null; then
        if docker ps -q -f name=easysight-worker-* | grep -q .; then
            execute_cmd "docker stop \$(docker ps -q -f name=easysight-worker-*)" "停止Docker容器"
            execute_cmd "docker rm \$(docker ps -aq -f name=easysight-worker-*)" "删除Docker容器"
        fi
    fi
    
    # 删除文件和目录
    if [[ -d "$INSTALL_DIR" ]]; then
        execute_cmd "rm -rf $INSTALL_DIR" "删除安装目录"
    fi
    
    if [[ -d "$CONFIG_DIR" ]]; then
        execute_cmd "rm -rf $CONFIG_DIR" "删除配置目录"
    fi
    
    # 删除用户
    if id "$USER" &>/dev/null; then
        execute_cmd "userdel $USER" "删除用户"
    fi
    
    log_success "EasySight Worker节点已卸载"
}

# 显示部署信息
show_deployment_info() {
    log_success "EasySight Worker节点部署完成！"
    
    echo
    echo "部署信息:"
    echo "  主节点地址: $MASTER_HOST:$MASTER_PORT"
    echo "  Worker名称: $WORKER_NAME"
    echo "  Worker池大小: $POOL_SIZE"
    echo "  安装目录: $INSTALL_DIR"
    echo "  配置目录: $CONFIG_DIR"
    echo "  日志目录: $LOG_DIR"
    echo
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        echo "Docker管理命令:"
        echo "  查看状态: docker ps -f name=easysight-worker-$WORKER_NAME"
        echo "  查看日志: docker logs easysight-worker-$WORKER_NAME"
        echo "  停止容器: docker stop easysight-worker-$WORKER_NAME"
        echo "  启动容器: docker start easysight-worker-$WORKER_NAME"
    elif [[ "$INSTALL_SYSTEMD" == "true" ]]; then
        echo "systemd管理命令:"
        echo "  启动服务: sudo systemctl start easysight-worker"
        echo "  停止服务: sudo systemctl stop easysight-worker"
        echo "  查看状态: sudo systemctl status easysight-worker"
        echo "  查看日志: sudo journalctl -u easysight-worker -f"
    else
        echo "手动启动命令:"
        echo "  cd $INSTALL_DIR && $INSTALL_DIR/venv/bin/python start_worker.py --config $CONFIG_DIR/worker.env"
    fi
    
    echo
}

# 主函数
main() {
    log_info "开始部署EasySight分布式Worker节点"
    
    parse_args "$@"
    
    if [[ "$UNINSTALL" == "true" ]]; then
        uninstall_worker
        exit 0
    fi
    
    check_requirements
    
    if [[ "$USE_DOCKER" == "true" ]]; then
        docker_deploy
    else
        setup_user_and_dirs
        install_dependencies
        copy_application
        create_config
        
        if [[ "$INSTALL_SYSTEMD" == "true" ]]; then
            install_systemd_service
        fi
    fi
    
    show_deployment_info
}

# 执行主函数
main "$@"