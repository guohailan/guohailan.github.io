# calico网络和flannel对比


本文介绍了k8s常见2中方案的差异，以及各自的优势
<!--more-->
## Calico
### 什么是Calico
Calico 是一个三层的数据中心网络方案,而且方便集成 OpenStack 这种 IaaS 云架构,能够提供高效可控的 VM、容器、裸机之间的通信。
### Calico网络基本架构
Calico BGP模式在小规模集群中可以直接互联,在大规模集群中可以通过额外的BGP route reflector来完成。
![Calico](/images/calico网络和flannel对比/calico.png " ")  
Calico是一个基于BGP的纯三层的网络方案,与OpenStack、Kubernetes、AWS、GCE等云平台都能够良好地集成。Calico在每个计算节点都利用Linux Kernel实现了一个高效的vRouter来负责数据转发。每个vRouter都通过BGP1协议把在本节点上运行的容器的路由信息向整个Calico网络广播,并自动设置到达其他节点的路由转发规则。Calico利用了Linux内核原生的路由和iptables防火墙功能。 进出各个容器、虚拟机和物理主机的所有流量都会在路由到目标之前遍历这些内核规则。
#### 主要组件

- **Felix**：Calico agent,跑在每台需要运行workload的节点上,主要负责配置路由及ACLs等信息来确保endpoint的连通状态；
- **etcd**：分布式键值存储,主要负责网络元数据一致性,确保Calico网络状态的准确性；
- **BGPClient(BIRD)**：主要负责把Felix写入kernel的路由信息分发到当前Calico网络,确保workload间的通信的有效性；
- **BGP Route Reflector(BIRD)**：大规模部署时使用,摒弃所有节点互联的mesh模式,通过一个或者多个BGPRoute Reflector来完成集中式的路由分发；
- **CalicoCtl**：允许从命令行界面配置实现高级策略和网络。

## Flannel
### 什么是Flannel
Flannel是由CoreOS开发的项目,可能是最直接和最受欢迎的CNI插件。它是容器编排系统中最成熟的网络结构示例之一,旨在实现更好的容器间和主机间网络。随着CNI概念的兴起,Flannel CNI插件算是早期的入门。
### Flannel网络基本架构
![Flannel](/images/calico网络和flannel对比/flannel.png " ")  
Flannel首先创建了一个名为Flannel0的网桥,而且这个网桥的一端连接docker0网桥,另一端连接一个叫作Flanneld的服务进程。Flanneld进程上连etcd,利用etcd来管理可分配的IP地址段资源,同时监控etcd中每个Pod的实际地址,并在内存中建立了一个Pod节点路由表；Flanneld进程下连docker0和物理网络,使用内存中的Pod节点路由表,将docker0发给它的数据包包装起来,利用物理网络的连接将数据包投递到目标Flanneld上,从而完成Pod到Pod之间的直接地址通信。
## 对比
Calico整个过程中始终都是根据iptables规则进行路由转发，并没有进行封包，解包的过程，这和Flannel比起来效率就会快多了。
由于Flannel几乎是最早的跨网络通信解决方案，其他的方案都可以被看做是Fannel的某种改进版。  

Calico的设计比较新颖，Flannel的Host-Gateway模式之所以不能跨二层网络，是因为它只能修改主机的路由，Calico把改路由表的做法换成了标准的BGP路由协议。
相当于在每个节点上模拟出一个额外的路由器，由于采用的是标准协议，Calico模拟路由器的路由表信息就可以被传播到网络的其他路由设备中，这样就实现了在三层网络上的高速跨节点网络。
不过在现实中的网络并不总是支持BGP路由的，因此Calico也设计了一种IPIP模式，使用Overlay的方式来传输数据。IPIP的包头非常小，而且也是内置在内核中的，因此它的速度理论上比VxLAN快一点点，但安全性更差。

## K8S为什么会出现各种网络方案
![net1](/images/calico网络和flannel对比/net.png " ")
> 由于Docker等容器工具只是利用内核的网络Namespace实现了网络隔离，各个节点上的容器是在所属节点上自动分配IP地址的，从全局来看，这种局部地址就像是不同小区里的门牌号，一旦拿到一个更大的范围上看，就可能是会重复的。  

![net2](/images/calico网络和flannel对比/net2.png " ")
> 为了解决这个问题，Flannel设计了一种全局的网络地址分配机制，即使用Etcd来存储网段和节点之间的关系，然后Flannel配置各个节点上的Docker（或其他容器工具），只在分配到当前节点的网段里选择容器IP地址。

![net3](/images/calico网络和flannel对比/net3.png " ")

![net4](/images/calico网络和flannel对比/net4.png " ")

![net5](/images/calico网络和flannel对比/net5.png " ")

