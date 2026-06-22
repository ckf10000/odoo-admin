# odoo-admin

#### Description

管理系统后台

#### Software Architecture

Software architecture description

#### Installation

1. 构建
    - 3.1 上传Dockerfile文件
    - 3.2 docker build -f ./Dockerfile -t odoo_admin:1.0.0 .
2. 部署
    - 3.1 宿主机添加odoo用户及项目目录
        - sudo groupadd -g 1002 odoo && sudo useradd -u 1002 -g odoo -m -s /bin/bash odoo
        - sudo mkdir -p /opt/odoo-admin/data && sudo mkdir -p /opt/odoo-admin/config && sudo mkdir -p
          /opt/odoo-admin/logs && sudo mkdir -p /opt/odoo-admin/nginx/conf
        - sudo usermod -aG docker odoo # 将 odoo 用户添加到 docker用户组
        - newgrp docker # 刷新组权限
    - 3.2 上传addons目录下的子文件、default.conf文件、odoo.linux.conf文件、docker-compose.yml文件
    - 3.3 如果服务器是首次部署odoo，需要初始化数据库，非首次部署，则跳过该步骤
        - 3.1.1 进入容器
            - docker run -it -e TZ=Asia/Shanghai --rm odoo_admin:1.0.0 /bin/sh
                - docker run：Docker 的核心命令，用于创建并启动一个新容器
                - -it：组合参数，表示以交互式终端模式运行容器
                    - -i（--interactive）：保持标准输入（STDIN）打开，允许用户与容器交互
                    - -t（--tty）：分配一个伪终端（pseudo-TTY），使容器像本地终端一样工作
                - e: 设置环境变量
                    - TZ: 设置容器中的时区，Asia/Shanghai为 上海时间（东八区）
                - --rm：容器退出后自动删除其文件系统，避免残留临时容器
                - /bin/sh：覆盖镜像的默认启动命令，启动一个 Shell 会话（通常是 Alpine 或精简镜像的默认 Shell）
        - 3.1.2 执行初始化命令
            - python /usr/local/bin/odoo -d odoo.master.dev --db_user admin --db_password admin --db_host
              192.168.200.200 --db_port 5432 --addons-path=/opt/odoo/addons --init all --without-demo all
              --stop-after-init
                - -d <database_name>：指定要初始化的数据库名称（如 test_db）
                - --db_*：数据库连接参数（用户、密码、主机、端口，默认端口为 5432）
                - --addons-path: 添加插件包路径
                - --init all：初始化所有内置模块。若需指定模块，可替换为 --init sale,purchase 等
                - --without-demo all：不加载演示数据。若需演示数据，则移除此参数
                - --stop-after-init: 初始化或更新模块后自动退出，不启动 HTTP 服务
    - 3.4 sudo chown -R odoo:odoo /opt/odoo-admin
    - 3.5 su - odoo && cd /opt/odoo-admin && compose up -d

#### Instructions

1. xxxx
2. xxxx
3. xxxx

#### Contribution

1. Fork the repository
2. Create Feat_xxx branch
3. Commit your code
4. Create Pull Request