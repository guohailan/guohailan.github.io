# kubeadm搭建k8s 1.18


本文主要介绍k8s搭建，使用官方推荐工具kubeadm进行搭建，ETCD独立部署
<!--more--> 

## docker 安装


添加阿里镜像源地址

```bash
yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo
```

安装docker出现如下错误,当前服务器上安装的containerd.io版本为1.2.0-3.el7版本过低

```bash
[root@guohailan3 ~]# yum -y install docker-ce
上次元数据过期检查：0:00:07 前，执行于 2020年05月24日 星期日 03时42分48秒。
错误：
 问题: package docker-ce-3:19.03.9-3.el7.x86_64 requires containerd.io >= 1.2.2-3, but none of the providers can be installed
  - cannot install the best candidate for the job
  - package containerd.io-1.2.10-3.2.el7.x86_64 is excluded
  - package containerd.io-1.2.13-3.1.el7.x86_64 is excluded
  - package containerd.io-1.2.13-3.2.el7.x86_64 is excluded
  - package containerd.io-1.2.2-3.3.el7.x86_64 is excluded
  - package containerd.io-1.2.2-3.el7.x86_64 is excluded
  - package containerd.io-1.2.4-3.1.el7.x86_64 is excluded
  - package containerd.io-1.2.5-3.1.el7.x86_64 is excluded
  - package containerd.io-1.2.6-3.3.el7.x86_64 is excluded
(尝试添加 '--skip-broken' 来跳过无法安装的软件包 或 '--nobest' 来不只使用最佳选择的软件包)
```

升级containerd.io，再次进行安装

```bash
wget https://download.docker.com/linux/centos/7/x86_64/edge/Packages/containerd.io-1.2.6-3.3.el7.x86_64.rpm
yum install containerd.io-1.2.6-3.3.el7.x86_64.rpm
```

配置开机启动和启动docker

```bash
systemctl enable docker
systemctl start docker
```

优化docker参数

[官方文档](https://kubernetes.io/zh/docs/setup/production-environment/container-runtimes/)表示，更改设置，令容器运行时和kubelet使用systemd作为cgroup驱动，以此使系统更为稳定。

```bash
tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://bk6kzfqm.mirror.aliyuncs.com"],
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
EOF
systemctl daemon-reload # 重新加载
systemctl restart docker # 重启docker
```

## kubernet 安装

### 安装kubectl

```bash
#无法连接google，配置了阿里的源
cat <<EOF > /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://mirrors.aliyun.com/kubernetes/yum/repos/kubernetes-el7-x86_64/
enabled=1
gpgcheck=0
EOF
yum install -y kubectl

setenforce 0 #暂时关闭selinux
sed -i 's/SELINUX=permissive/SELINUX=disabled/' /etc/sysconfig/selinux #Kubernetes 1.8开始要求关闭系统的Swap，如果不关闭，默认配置下kubelet将无法启动。
swapoff -a
yum install -y kubeadm kubelet #安装kubeadm kubelet工具
```

### 准备证书

证书需要在一台机器上生成，拷贝到别的机器上

#### 准备证书管理工具

```bash
wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
chmod +x cfssl_linux-amd64
mv cfssl_linux-amd64 /usr/bin/cfssl

wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64
chmod +x cfssljson_linux-amd64
mv cfssljson_linux-amd64 /usr/bin/cfssljson

wget https://pkg.cfssl.org/R1.2/cfssl-certinfo_linux-amd64
chmod +x cfssl-certinfo_linux-amd64
mv cfssl-certinfo_linux-amd64 /usr/bin/cfssl-certinfo
```

#### 生成ETCD的TLS 秘钥和证书

```bash
# 创建 CA 配置文件
mkdir ssl && cd ssl
cfssl print-defaults csr > csr.json
cat > config.json <<EOF
{
"signing": {
    "default": {
      "expiry": "8760h"
      },
    "profiles": {
      "kubernetes": {
        "usages": [
            "signing",
            "key encipherment",
            "server auth",
            "client auth"
        ],
        "expiry": "8760h"
      }
    }
}
}
EOF
```

- config.json：可以定义多个 profiles，分别指定不同的过期时间、使用场景等参数；后续在签名证书时使用某个 profile；
- signing：表示该证书可用于签名其它证书；生成的 ca.pem 证书中 CA=TRUE；
- server auth：表示 client 可以用该 CA 对 server 提供的证书进行验证；
- client auth：表示 server 可以用该 CA 对 client 提供的证书进行验证；

#### 创建ca证书请求

```bash
cat > ca-csr.json <<EOF
{
    "CN": "kubernetes",
    "key": {
        "algo": "rsa",
        "size": 2048
    },
    "names": [
        {
            "C": "CN",
            "L": "GuangDong",
            "ST": "ShenZhen",
            "O": "k8s",
            "OU": "System"
        }
    ]
}
EOF
```

- "CN"：Common Name，kube-apiserver 从证书中提取该字段作为请求的用户名 (User Name)；浏览器使用该字段验证网站是否合法；
- "O"：Organization，kube-apiserver 从证书中提取该字段作为请求用户所属的组 (Group)；

#### 创建CA证书和私钥

```bash
cfssl gencert -initca ca-csr.json | cfssljson -bare ca
```

#### 创建 etcd 证书签名请求

```bash
cat > etcd-csr.json <<EOF
{
  "CN": "etcd",
  "hosts": [
    "192.168.31.48",
    "192.168.31.137",
    "192.168.31.226"
  ],
  "key": {
    "algo": "rsa",
    "size": 2048
  },
  "names": [
    {
      "C": "CN",
      "ST": "GuangDong",
      "L": "ShenZhen",
      "O": "k8s",
      "OU": "System"
    }
  ]
}
EOF
```

- hosts 字段指定授权使用该证书的 etcd 节点 IP；
- 每个节点IP 都要在里面 或者 每个机器申请一个对应IP的证书

#### 生成 etcd 证书和私钥

```bash
cfssl gencert -ca=ca.pem \
  -ca-key=ca-key.pem \
  -config=config.json \
  -profile=kubernetes etcd-csr.json | cfssljson -bare etcd
```

#### 将证书拷贝到所有服务器的指定目录

```bash
mkdir -p /etc/etcd/ssl
cp etcd.pem etcd-key.pem  ca.pem /etc/etcd/ssl/
```

### 安装ETCD

#### 准备二进制文件

```bash
wget https://github.com/coreos/etcd/releases/download/v3.4.9/etcd-v3.4.9-linux-amd64.tar.gz
tar -vxf etcd-v3.4.9-linux-amd64.tar.gz
cp etcd-v3.4.9-linux-amd64/etcd* /usr/bin/
chmod +x /usr/bin/etcd*
```

#### 部署环境变量

```bash
export NODE_NAME="etcd-host1" #当前部署的机器名称(随便定义，只要能区分不同机器即可)
export NODE_IP="192.168.31.48" # 当前部署的机器 IP
export export NODE_IPS="192.168.31.48 192.168.31.137 192.168.31.226" # etcd 集群所有机器 IP
# etcd 集群间通信的IP和端口
export ETCD_NODES="etcd-host1=https://192.168.31.48:2380,etcd-host2=https://192.168.31.137:2380,etcd-host3=https://192.168.31.226:2380"
```

#### 创建etcd的systemd unit文件

```bash
mkdir -p /var/lib/etcd  # 必须先创建工作目录
cat > etcd.service <<EOF
[Unit]
Description=Etcd Server
After=network.target
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
WorkingDirectory=/var/lib/etcd/
ExecStart=/usr/bin/etcd \\
  --name=${NODE_NAME} \\
  --cert-file=/etc/etcd/ssl/etcd.pem \\
  --key-file=/etc/etcd/ssl/etcd-key.pem \\
  --peer-cert-file=/etc/etcd/ssl/etcd.pem \\
  --peer-key-file=/etc/etcd/ssl/etcd-key.pem \\
  --trusted-ca-file=/etc/etcd/ssl/ca.pem \\
  --peer-trusted-ca-file=/etc/etcd/ssl/ca.pem \\
  --initial-advertise-peer-urls=https://${NODE_IP}:2380 \\
  --listen-peer-urls=https://${NODE_IP}:2380 \\
  --listen-client-urls=https://${NODE_IP}:2379,http://127.0.0.1:2379 \\
  --advertise-client-urls=https://${NODE_IP}:2379 \\
  --initial-cluster-token=etcd-cluster-0 \\
  --initial-cluster=${ETCD_NODES} \\
  --initial-cluster-state=new \\
  --data-dir=/var/lib/etcd
Restart=on-failure
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
```

- --name：方便理解的节点名称，默认为 default，在集群中应该保持唯一，可以使用 hostname
- --data-dir：服务运行数据保存的路径，默认为 ${name}.etcd
- --snapshot-count：指定有多少事务（transaction）被提交时，触发截取快照保存到磁盘
- --heartbeat-interval：leader 多久发送一次心跳到 followers。默认值是 100ms
- --eletion-timeout：重新投票的超时时间，如果 follow 在该时间间隔没有收到心跳包，会触发重新投票，默认为 1000 ms
- --listen-peer-urls：和同伴通信的地址，比如 http://ip:2380，如果有多个，使用逗号分隔。需要所有节点都能够访问，所以不要使用 localhost！
- --listen-client-urls：对外提供服务的地址：比如 http://ip:2379,http://127.0.0.1:2379，客户端会连接到这里和 etcd 交互
- --advertise-client-urls：对外公告的该节点客户端监听地址，这个值会告诉集群中其他节点
- --initial-advertise-peer-urls：该节点同伴监听地址，这个值会告诉集群中其他节点
- --initial-cluster：集群中所有节点的信息，格式为 node1=http://ip1:2380,node2=http://ip2:2380,…。注意：这里的 node1 是节点的 –name 指定的名字；后面的 ip1:2380 是 –initial-advertise-peer-urls 指定的值
- --initial-cluster-state：新建集群的时候，这个值为 new；假如已经存在的集群，这个值为 existing
- --initial-cluster-token：创建集群的 token，这个值每个集群保持唯一。这样的话，如果你要重新创建集群，即使配置和之前一样，也会再次生成新的集群和节点 uuid；否则会导致多个集群之间的冲突，造成未知的错误

#### 启动 etcd 服务

```bash
mv etcd.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable etcd
systemctl start etcd
systemctl status etcd
```

#### 验证服务并配置etcdctl工具

```bash
etcdctl --endpoints="https://192.168.31.48:2379,https://192.168.31.137:2379,https://192.168.31.226:2379" --cacert=/etc/etcd/ssl/ca.pem --cert=/etc/etcd/ssl/etcd.pem --key=/etc/etcd/ssl/etcd-key.pem endpoint health
```

为了后续操作方便可配置alias

```bash
alias etcdctl='etcdctl --cacert=/etc/etcd/ssl/ca.pem --cert=/etc/etcd/ssl/etcd.pem --key=/etc/etcd/ssl/etcd-key.pem --endpoints="https://192.168.31.48:2379,https://192.168.31.137:2379,https://192.168.31.226:2379"'
```

### 初始化master

#### 创建master配置文件

```bash
cat > /etc/kubernetes/config.yaml  <<EOF
apiVersion: kubeadm.k8s.io/v1beta1
# 国内不能访问 Google，修改为阿里云
imageRepository: registry.aliyuncs.com/google_containers
kind: ClusterConfiguration
### etcd 配置及秘钥 ###
etcd:
  external:
    endpoints:
    - https://192.168.31.48:2379
    - https://192.168.31.137:2379
    - https://192.168.31.226:2379
    caFile: /etc/etcd/ssl/ca.pem
    certFile: /etc/etcd/ssl/etcd.pem
    keyFile: /etc/etcd/ssl/etcd-key.pem
    dataDir: /var/lib/etcd
### calico 网络插件的子网 ###
networking:
  podSubnet: "10.0.0.0/16"
  serviceSubnet: "10.96.0.0/12"
###k8s的版本###
kubernetesVersion: 1.18.0
EOF
```

#### 初始化master

可查看依赖的镜像版本

```bash
kubeadm config images list --kubernetes-version=v1.18.0
```

```bash
kubeadm init --config /etc/kubernetes/config.yaml #主节点进行初始化
```

出现如下提示表示配置成功

```bash
Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:
  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

Then you can join any number of worker nodes by running the following on each as root:
kubeadm join 192.168.31.226:6443 --token v7b8zo.5hc1au8vl96xqyie \
    --discovery-token-ca-cert-hash sha256:908597386cd0311f24e2d7c95e40559e3137523078e69e1262643c6161abc10a
```

如果出现如下错误，需要按照上图提示，配置kube/config

![image-20200815180231821](/images/kubeadm搭建k8s-1-18/image-20200815180231821.png " ")

##### 多master初始化

如果希望部署多master需要用下面的配置文件，token和tokenTTL在初始化第一台master的时候注释掉

```bash
cat > /etc/kubernetes/config.yaml  <<EOF
apiVersion: kubeadm.k8s.io/v1beta1
# 国内不能访问 Google，修改为阿里云
imageRepository: registry.aliyuncs.com/google_containers
kind: ClusterConfiguration
### etcd 配置及秘钥 ###
etcd:
  external:
    endpoints:
    - https://192.168.31.48:2379
    - https://192.168.31.137:2379
    - https://192.168.31.226:2379
    caFile: /etc/etcd/ssl/ca.pem
    certFile: /etc/etcd/ssl/etcd.pem
    keyFile: /etc/etcd/ssl/etcd-key.pem
    dataDir: /var/lib/etcd
### calico 网络插件的子网 ###
networking:
  podSubnet: "10.0.0.0/16"
  serviceSubnet: "10.96.0.0/12"
###k8s的版本###
kubernetesVersion: 1.18.0
######多master配置#######
#下面的token是master1节点初始化完成后，join得到的token值
token: "1gddb4.cs1chtdrk5r9aa0i"
tokenTTL: "0s"
#是kubeadm帮我们apiserver生成对外服务的证书用的。因为外部访问apiserver是通过负载均衡实现的，所以作为服务端提供的证书中应该写的hosts是负载均衡的地址。
apiServerCertSANs:
#允许访问apiserver的地址
- 192.168.30.189 #apiserver的负载均衡ip，或者是slb的ip
- k8s-master1
- k8s-slave1
- k8s-slave2
- 192.168.31.48
- 192.168.31.137
- 192.168.31.226
apiServerExtraArgs:
 apiserver-count: "3"
 endpoint-reconciler-type: lease
EOF
```

## calico安装

安装calico

```bash
kubectl apply -f https://docs.projectcalico.org/v3.15/manifests/calico.yaml
https://docs.projectcalico.org/manifests/calico-etcd.yaml
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

查看节点启动详情，calico3个进程都启动完毕

![image-20200815183600446](/images/kubeadm搭建k8s-1-18/image-20200815183600446.png " ")

## 添加node节点

在另一台节点执行下面命令，加入集群

```bash
kubeadm join 192.168.31.226:6443 --token v7b8zo.5hc1au8vl96xqyie     --discovery-token-ca-cert-hash sha256:908597386cd0311f24e2d7c95e40559e3137523078e69e1262643c6161abc10a
```

出现如下提示表示加入成功

![image-20200815181858759](/images/kubeadm搭建k8s-1-18/image-20200815181858759.png " ")

在master执行`kubectl get nodes`，看到node状态都是Ready表示搭建完成

![image-20200815183942023](/images/kubeadm搭建k8s-1-18/image-20200815183942023.png " ")
