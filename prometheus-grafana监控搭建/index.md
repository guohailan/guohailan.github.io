# prometheus+grafana监控搭建

本文主要介绍prometheus+grafana+consul方案监控系统的搭建，本次搭建采用虚拟机方式进行搭建，采取consul进行服务注册
<!--more-->
## prometheus安装与配置
### 介绍与基本架构
prometheus是由谷歌研发的一款开源的监控软件，目前已经被云计算本地基金会托管，是继k8s托管的第二个项目。
![](/images/prometheus+grafana监控搭建/prometheus.png " ")
prometheus根据配置定时去拉取各个节点的数据，默认使用的拉取方式是pull，也可以使用pushgateway提供的push方式获取各个监控节点的数据。将获取到的数据存入TSDB，一款时序型数据库。此时prometheus已经获取到了监控数据，可以使用内置的PromQL进行查询。它的报警功能使用Alertmanager提供，Alertmanager是prometheus的告警管理和发送报警的一个组件。prometheus原生的图标功能过于简单，可将prometheus数据接入grafana，由grafana进行统一管理。
### 安装Prometheus Server
首先从官网下载Prometheus安装程序
![](/images/prometheus+grafana监控搭建/prometheusdownload.png " ")
```bash
wget https://github.com/prometheus/prometheus/releases/download/v2.18.1/prometheus-2.18.1.linux-amd64.tar.gz
```
执行执行解压命令
```bash
tar -vxf prometheus-2.18.1.linux-amd64.tar.gz
```
编辑解压目录下的prometheus.yml，执行命令：`vi prometheus.yml`进行基本配置
```bash
[root@guohailan1 prometheus-2.18.1.linux-amd64]# cat prometheus.yml
# my global config
global:
  scrape_interval: 10s #每10s采集一次数据
  evaluation_interval: 10s #每10s做一次告警检测
  scrape_timeout: 5s #拉取一个 target 的超时时间
alerting: #Alertmanager 相关配置暂时未配置
  alertmanagers:
  - static_configs:
    - targets:
rule_files:
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
    - targets: ['localhost:9090']
  - job_name: 'linux-exporter'
    metrics_path: /metrics
    static_configs:
    - targets: ['192.168.31.48:9100']
```
配置开机启动，在CentOS8下官方推荐使用systemctl进行开机自启管理
```bash
cat << EOF > /usr/lib/systemd/system/prometheus.service
[Unit]
Description=Prometheus
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c "/prometheus/prometheus-2.18.1.linux-amd64/prometheus --web.enable-lifecycle --storage.local.retention 24h0m0s --config.file=/prometheus/prometheus-2.18.1.linux-amd64/prometheus.yml"

[Install]
WantedBy=multi-user.target
EOF
```
设置自启动和启动prometheus
```bash
systemctl enable prometheus
systemctl start prometheus
```
浏览器端访问`http://192.168.31.48:9090/graph`，如果出现界面表示搭建成功,如果服务器上有防火墙，可能需要先关闭防火墙或者配置规则
![9090](/images/prometheus+grafana监控搭建/9090.png " ")
## node_exporter安装
node-exporter用于采集服务器层面的运行指标，包括机器的loadavg、filesystem、meminfo等基础监控，类似于传统主机监控维度的zabbix-agent。node-export由prometheus官方提供、维护，不会捆绑安装，但基本上是必备的exporter。
![](/images/prometheus+grafana监控搭建/node_exporter.png " ")
从prometheus官网下载相应版本的node_exporter
```bash
wget https://github.com/prometheus/consul_exporter/releases/download/v0.6.0/consul_exporter-0.6.0.linux-amd64.tar.gz
```
配置开机启动
```bash
cat << EOF > /usr/lib/systemd/system/node_exporter.service
[Unit]
Description=node_exporter
After=network.target 

[Service]
Type=simple
ExecStart=/bin/bash -c "/root/exporter/node_exporter-1.0.0-rc.1.linux-amd64/node_exporter"

[Install]
WantedBy=multi-user.target

EOF
```
## consul
### 安装consul
Consul 是一个支持多数据中心分布式高可用的服务发现和配置共享的服务软件,由 HashiCorp 公司用 Go 语言开发, 基于 Mozilla Public License 2.0 的协议进行开源. Consul 支持健康检查,并允许 HTTP 和 DNS 协议调用 API 存储键值对.命令行超级好用的虚拟机管理软件 vgrant 也是 HashiCorp 公司开发的产品.一致性协议采用 Raft 算法,用来保证服务的高可用. 使用 GOSSIP 协议管理成员和广播消息, 并且支持 ACL 访问控制.

首先从官网上下载consul最新版本并且解压
```bash
wget https://releases.hashicorp.com/consul/1.7.3/consul_1.7.3_linux_amd64.zip
unzip consul_1.7.3_linux_amd64.zip
```
本案例搭建为单机版本,将下列命令写入start.sh
```bash
consul agent -data-dir /prometheus/consul/data -bind=172.0.0.1 -datacenter=dc1 -ui -client=0.0.0.0 -server -http-port=8500 -bootstrap-expect=1
```
配置开机启动
```bash
cat << EOF > /usr/lib/systemd/system/consul.service
[Unit]
Description=consul
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c "/prometheus/consul/start.sh"

[Install]
WantedBy=multi-user.target
EOF
```
访问http://localhost:8500 ,能出现界面表示搭建成功
![](/images/prometheus+grafana监控搭建/consul.png " ")
### consul注册与删除
在服务器上使用如下命令将node_exporter,注册成功后可以看到consul界面上出现了注册的信息，Node Checks和Service Checks绿色表示node_exporter状态正常，点击可查看详情
```bash
curl -X PUT -d '{"id": "192.168.31.48","name": "node-exporter","address": "192.168.31.48","port": 9100,"tags": ["guohailan1"],"checks": [{"http": "http://192.168.31.48:9100/metrics", "interval": "5s"}]}'  http://192.168.31.48:8500/v1/agent/service/register
```
![](/images/prometheus+grafana监控搭建/register.png " ")
如果注册错误或者不使用了可用如下命令删除注册信息
```bash
curl -X PUT http://192.168.31.48:8500/v1/agent/service/deregister/node-exporter 
```
###prometheus对接consul
修改prometheus配置文件`vi /prometheus/prometheus-2.18.1.linux-amd64/prometheus.yml`
```bash
# my global config
global:
  scrape_interval: 10s
  evaluation_interval: 10s
  scrape_timeout: 5s
alerting:
  alertmanagers:
  - static_configs:
    - targets:
rule_files:
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
    - targets: ['localhost:9090']
  - job_name: 'consul-prometheus'
    consul_sd_configs:
    - server: '192.168.31.48:8500' #consul地址
      services: []
    relabel_configs:
    - source_labels: [__meta_consul_service_port] #prometheus将对匹配上的lables进行操作
      regex: 9100
      action: keep
```
详细 relabel_configs 配置及说明可以参考 relabel_config 官网说明，这里我简单列举一下里面每个 relabel_action 的作用，方便下边演示。
- replace: 根据 regex 的配置匹配 source_labels 标签的值（注意：多个 source_label 的值会按照 separator 进行拼接），并且将匹配到的值写入到 target_label 当中，如果有多个匹配组，则可以使用 ${1}, ${2} 确定写入的内容。如果没匹配到任何内容则不对 target_label 进行重新， 默认为 replace。
- keep: 丢弃 source_labels 的值中没有匹配到 regex 正则表达式内容的 Target 实例
- drop: 丢弃 source_labels 的值中匹配到 regex 正则表达式内容的 Target 实例
- hashmod: 将 target_label 设置为关联的 source_label 的哈希模块
- labelmap: 根据 regex 去匹配 Target 实例所有标签的名称（注意是名称），并且将捕获到的内容作为为新的标签名称，regex 匹配到标签的的值作为新标签的值
- labeldrop: 对 Target 标签进行过滤，会移除匹配过滤条件的所有标签
- labelkeep: 对 Target 标签进行过滤，会移除不匹配过滤条件的所有标签

配置完成重启promethus即可看到targets上有新的node_exporter信息，其中Labels中的指标即上一步配置中的 "source_labels"
![](/images/prometheus+grafana监控搭建/targets.png " ")
## grafana
grafana是一个非常酷的数据可视化平台，常常应用于显示监控数据，底层数据源可以支持influxDb、graphite、elasticSeach。  
### 安装grafana
首先还是从[官网](https://grafana.com/grafana/download)下载安装包,进行安装
```bash
wget https://dl.grafana.com/oss/release/grafana-7.0.1-1.x86_64.rpm
sudo yum install grafana-7.0.1-1.x86_64.rpm
systemctl enable grafana-server.service #允许开机启动
systemctl start grafana-server.service #启动grafana
```
启动服务之后：http://localhost:3000 。用户名和密码在初始化都是admin和admin
![](/images/prometheus+grafana监控搭建/grafana.png " ")
### 配置grafana
#### 数据源
首先配置数据源,选择之前搭建的prometheus的连接串，点击保存
![](/images/prometheus+grafana监控搭建/data_sources.png " ")
#### dashboard
grafana[官网](https://grafana.com/grafana/dashboards?orderBy=name&direction=asc)有很多大神的作品，可以直接使用
![](/images/prometheus+grafana监控搭建/dashboards.png " ")
grafana支持很多中导入方式，上传json文件或者直接贴json配置，这里因可以使用外网，直接复制模板ID，导入到grafana中
![](/images/prometheus+grafana监控搭建/import.png " ")
导入完成后，即可看到报表信息
![](/images/prometheus+grafana监控搭建/view.png " ")
