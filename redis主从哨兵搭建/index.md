# Redis主从哨兵搭建


本文章基于最新版本Redis5.0.5版本进行redis主从哨兵模式搭建
<!--more-->
## Redis 简介
Redis 是一个开源（BSD许可）的，内存中的数据结构存储系统，它可以用作数据库、缓存和消息中间件. 它支持多种类型的数据结构，如字符串（strings），散列（hashes），列表（lists），集合（sets），有序集合（sorted sets）与范围查询，bitmaps，hyperloglogs 和 地理空间（geospatial）索引半径查询. Redis 内置了复制（replication），LUA脚本（Lua scripting），LRU驱动事件（LRU eviction），事务（transactions）和不同级别的磁盘持久化（persistence），并通过Redis哨兵（Sentinel）和自动分区（Cluster）提供高可用性（high availability）.为了实现其卓越的性能，Redis采用运行在内存中的数据集工作方式.根据您的使用情况，您可以每隔一定时间将数据集导出到磁盘，或者追加到命令日志中. 您也可以关闭持久化功能，将Redis作为一个高效的网络的缓存数据功能使用.
## 集群规划
搭建redis需要1个主节点，且还有2个从节点，所以至少需要配置3个节点。因虚拟机是2台，所以通过配置不同端口的方式，在第一台机器上启动1个主节点，第二台上启动2个从节点，3个节点上分别启动sentinel
## 源码编译安装
首先进入redis[官网](http://www.redis.cn)下载最新版本的redis，源码编译安装,源码安装需要依赖gcc、gcc-c++，如果出现`gcc：命令未找到`等错误，请先安装对应的依赖
```bash
wget http://download.redis.io/releases/redis-5.0.5.tar.gz
tar -zvxf redis-5.0.5.tar.gz
make MALLOC=libc #虚拟机只分配了一核所以未使用-j参数
mkdir -p /usr/local/redis #创建redis安装目录
make PREFIX=/usr/local/redis install
```
redis启动的时候会占用一个终端，这是因为没有指定redis.conf文件，启动的时候是按默认进行的。所以如果不想使其占用，我们可以修改 redis.conf 配置文件，修改`daemonize no` 为 `daemonize yes`，然后再指定配置文件启动redis服务
![](/images/Redis主从哨兵搭建/daemonize.png " ")
然后启动redis进程
```bash
/usr/local/redis/bin/redis-server /usr/local/redis/conf/redis.conf
```
查看端口和使用`redis-cli`连接redis，启动正常
![](/images/Redis主从哨兵搭建/start.png " ")
## 集群配置
### master
创建`/usr/local/redis/conf`目录，用于存放redis的配置文件。在`conf`目录下创建`6379`目录，修改好的配置文件`redis.conf`放到目录下
```bash
port 6379 # 端口6379
bind 本机ip # 默认ip为127.0.0.1 需要改为其他节点机器可访问的ip 否则创建集群时无法访问对应的端口，无法创建集群
daemonize yes # redis后台运行
pidfile /var/run/redis_6379.pid # pidfile文件对应6379
appendonly yes # aof日志开启 有需要就开启，它会每次写操作都记录一条日志
appendfilename appendonly.aof # aof日志文件名
logfile /tmp/redis-6379.log # redis日志路径
```
先kill掉原来验证的单节点进程，然后启动master
```bash
/usr/local/redis/bin/redis-server /usr/local/redis/conf/6379/redis.conf
netstat -anp|grep tcp|grep -E '6379' #查看监听端口是否启动
```
![](/images/Redis主从哨兵搭建/cluster_start.png " ")

### slave 
创建`/usr/local/redis/conf`目录，用于存放redis的配置文件。在`conf`目录下创建`6379`、`6380`目录，修改好的配置文件`redis.conf`放到目录下
```bash
port 6379 # 端口6379、6380
bind 本机ip # 默认ip为127.0.0.1 需要改为其他节点机器可访问的ip 否则创建集群时无法访问对应的端口，无法创建集群
daemonize yes # redis后台运行
pidfile /var/run/redis_6379.pid # pidfile文件对应6379、6380
appendonly yes # aof日志开启 有需要就开启，它会每次写操作都记录一条日志
appendfilename appendonly.aof # aof日志文件名
logfile /tmp/redis-6379.log # redis日志路径
replicaof 192.168.31.137 6379 #master节点的ip和端口
```
然后启动slave
```bash
/usr/local/redis/bin/redis-server /usr/local/redis/conf/6379/redis.conf
/usr/local/redis/bin/redis-server /usr/local/redis/conf/6380/redis.conf
```
### sentinel 
复制安装包中的`sentinel.conf`文件到redis的配置文件目录下，修改配置文件,将配置文件分别复制到对应的目录
```bash
port 26379 # 端口26379、26380
bind 本机ip # 默认ip为127.0.0.1 需要改为其他节点机器可访问的ip 否则创建集群时无法访问对应的端口，无法创建集群
daemonize yes # redis后台运行
pidfile /var/run/sentinel_26379.pid # pidfile文件对应6379、6380
logfile /tmp/redis-26379.log # redis日志路径
sentinel down-after-milliseconds mymaster 30000 #master或slave多长时间（默认30秒）不能使用后标记为s_down状态
sentinel monitor mymaster 192.168.31.137 6379 2 #监听的master的集群名和节点，这个后面的数字2,是指当有两个及以上的sentinel服务检测到master宕机，才会去执行主从切换的功能
sentinel parallel-syncs mymaster 1 #指定了在发生failover主备切换时最多可以有多少个slave同时对新的master进行同步，这个数字越小，完成failover所需的时间就越长，但是如果这个数字越大，就意味着越多的slave因为replication而不可用
```
启动sentinel
```bash
/usr/local/redis/bin/redis-sentinel /usr/local/redis/conf/6379/sentinel.conf
/usr/local/redis/bin/redis-sentinel /usr/local/redis/conf/6380/sentinel.conf
```
查看sentinel启动状态
![](/images/Redis主从哨兵搭建/sentinel.png " ")

## 故障迁移测试
连接redis集群`/usr/local/redis/bin/redis-cli -c -h 192.168.31.226 -p 6379`,查询当前master信息，当前集群有2个slave
![](/images/Redis主从哨兵搭建/master_info.png " ")
模拟当前master故障，杀掉master进程
![](/images/Redis主从哨兵搭建/kill_master.png " ")
再次连接redis集群发现master已经进行了重新选举，选出了新的master
![](/images/Redis主从哨兵搭建/master_info2.png " ")
