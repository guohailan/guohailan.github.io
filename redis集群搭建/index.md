# Redis集群搭建


Redis3.0上加入了cluster模式，实现的redis的分布式存储，本文主要介绍Redis集群的相关搭建。
<!--more-->

## 集群特点

redis的哨兵模式基本已经可以实现高可用，读写分离 ，但是在这种模式下每台redis服务器都存储相同的数据，很浪费内存，所以在redis3.0上加入了cluster模式，实现的redis的分布式存储，也就是说每台redis节点上存储不同的内容。

 Redis-Cluster采用无中心结构,它的特点如下：

- 所有的redis节点彼此互联(PING-PONG机制),内部使用二进制协议优化传输速度和带宽。
- 节点的fail是通过集群中超过半数的节点检测失效时才生效。
- 客户端与redis节点直连,不需要中间代理层.客户端不需要连接集群所有节点,连接集群中任何一个可用节点即可。

**工作方式：**

在redis的每一个节点上，都有这么两个东西，一个是插槽（slot），它的的取值范围是：0-16383。还有一个就是cluster，可以理解为是一个集群管理的插件。当我们的存取的key到达的时候，redis会根据crc16的算法得出一个结果，然后把结果对 16384 求余数，这样每个 key 都会对应一个编号在 0-16383 之间的哈希槽，通过这个值，去找到对应的插槽所对应的节点，然后直接自动跳转到这个对应的节点上进行存取操作。

为了保证高可用，redis-cluster集群引入了主从模式，一个主节点对应一个或者多个从节点，当主节点宕机的时候，就会启用从节点。当其它主节点ping一个主节点A时，如果半数以上的主节点与A通信超时，那么认为主节点A宕机了。如果主节点A和它的从节点A1都宕机了，那么该集群就无法再提供服务了。

## 集群规划

搭建redis最少需要6个节点。因虚拟机是2台，所以通过配置不同端口的方式，在第一台机器上启动3个节点，第二台上启动3个节点

| IP             | 端口 |
| -------------- | ---- |
| 192.168.31.226 | 6379 |
| 192.168.31.226 | 6380 |
| 192.168.31.226 | 6381 |
| 192.168.31.137 | 6379 |
| 192.168.31.137 | 6380 |
| 192.168.31.137 | 6381 |



## 集群配置

本文默认认为已经会安装redis，搭建部分不再赘述。需要可参考之前文章[Redis主从哨兵搭建](https://guohailan.github.io/redis主从哨兵搭建/#源码编译安装)安装部分

创建`/usr/local/redis/conf_cluster`目录，用于存放redis的配置文件。在`conf_cluster`目录下创建`6379`、`6380`、`6381`目录，修改好的配置文件`redis.conf`分别放到对应目录下
```bash
port 6379 # 端口6379 6380 6381
bind 192.168.31.226 # 默认ip为127.0.0.1 需要改为其他节点机器可访问的ip 否则创建集群时无法访问对应的端口，无法创建集群
daemonize yes # redis后台运行
cluster-enabled yes # 开启集群
pidfile "/usr/local/redis/conf_cluster/6379/redis.pid" # pidfile文件对应6379 6380 6381
appendonly yes # aof日志开启 有需要就开启，它会每次写操作都记录一条日志
dir "/usr/local/redis/conf_cluster" # 设置redis数据写入目录
appendfilename appendonly.aof # aof日志文件名
logfile /tmp/redis-6379.log # redis日志路径对应6379 6380 6381
```

启动redis全部节点

```bash
/usr/local/redis/bin/redis-server /usr/local/redis/conf_cluster/6379/redis.conf
/usr/local/redis/bin/redis-server /usr/local/redis/conf_cluster/6380/redis.conf
/usr/local/redis/bin/redis-server /usr/local/redis/conf_cluster/6381/redis.conf
netstat -anp|grep tcp|grep -E '6379|6380|6381' #查看监听端口是否启动
```

## 创建集群

用redis-cli创建整个redis集群(redis5以前的版本集群是依靠ruby脚本redis-trib.rb实现)

```bash
/usr/local/redis/bin/redis-cli -a 1234 --cluster create --cluster-replicas 1 192.168.31.226:6379 192.168.31.226:6380 192.168.31.226:6381 192.168.31.137:6379 192.168.31.137:6380 192.168.31.137:6381 # -a 表示使用密码 --cluster-replicas 1表示为每个主节点创建一个副本
```

![](/images/Redis集群搭建/join.png " ")

使用`redlis-cli`连接任意节点，`cluster info` 和 `cluster nodes`可查看当前集群状态，此时集群搭建成功

![](/images/Redis集群搭建/info.png " ")


