# Trojan-go搭建


使用trojan-go进行搭建。
<!--more-->

## 什么是Trojan-go

使用Go实现的完整Trojan代理，与Trojan协议以及Trojan版本的配置文件格式兼容。安全，高效，轻巧，易用。详见[官网](https://github.com/p4gefau1t/trojan-go)

## 域名准备

域名申请可以去腾讯云或者阿里云等国内大厂申请（缺点就是需要花钱），这里我是去的免费域名商freenom申请的[http://www.freenom.com/zh/index.html](http://www.freenom.com/zh/index.html)，不过访问这个地址很慢，所以可能需要提前出去。

### 域名申请

首先注册账号，基本信息里实测国家选择<font color=#DC143C>美国</font>以外的地区可能无法注册成功，所以这里我选择的洛杉矶

![](/images/Trojan-go搭建/image-20210118221317622.png " ")

输入希望申请的域名，点击检查可用性

![](/images/Trojan-go搭建/image-20210118220651867.png " ")

选择心仪的域名后缀，点击现在获取

![](/images/Trojan-go搭建/image-20210118220757391.png " ")

域名时长我们一般选择最长时间1年，然后将VPS的IP填入解析地址（也可以现在不填，申请完成后在My Domains里面进行填写）

![](/images/Trojan-go搭建/image-20210118222157926.png " ")

### 域名测试

默认的DNS生效时间比较长，大概半小时左右。本地能ping通域名，返回的地址为希望的IP，表示域名申请成功

![](/images/Trojan-go搭建/image-20210118222954624.png " ")

## 证书申请

**<font color=#DC143C>一键搭建脚本可以自动申请证书（有效期3个月），证书申请步骤可以跳过</font>**

证书申请也是本着不花钱的原则，选择[https://freessl.cn/](https://freessl.cn/)

因为只有亚洲诚信可以支持双域名，而且有效期可以1年，所以选择亚洲诚信，点击创建免费的SSL证书

![](/images/Trojan-go搭建/image-20210118223321305.png " ")

填入个人邮箱，然后点击创建

![](/images/Trojan-go搭建/image-20210118223513080.png " ")

登录FreeSSL的账号，安装亚洲诚信的KeyManager

![](/images/Trojan-go搭建/image-20210118223709924.png " ")

点击继续后，会自动带起KeyManager，生成秘钥

![](/images/Trojan-go搭建/image-20210118223957243.png " ")

回到浏览器，在浏览器上会提示DNS验证

![](/images/Trojan-go搭建/image-20210118224709956.png " ")

这时我们回到freenom点击My Domains，点击Manage Domain，选择Manage Freenom DNS

![](/images/Trojan-go搭建/image-20210118224205751.png " ")

将证书生成的信息填入DNS的解析里面，Type选择TXT，然后点击保存

![](/images/Trojan-go搭建/image-20210118224559935.png " ")

回到freessl页面，点击配置完成（可能有30分钟左右延迟），检测一下，当检测通过，点击验证即可签发证书，证书签发以后，可以使用https访问一下自己的域名，可以看到证书是有效的

![](/images/Trojan-go搭建/image-20210118230001432.png " ")

## Torjan-go搭建

**此处我使用的是Centos7的系统**

首先安装依赖包

```shell
yum update -y && yum install -y curl
```

### 安装BBR加速

```shell
wget -N --no-check-certificate "https://raw.githubusercontent.com/chiakge/Linux-NetSpeed/master/tcp.sh" && chmod +x tcp.sh && ./tcp.sh
```

选择需要的BBR加速内核，我的服务器默认已经安装了BBR内核，因此我直接选择4开启

### 一键安装trojan-go



```shell
#安装/更新
source <(curl -sL https://git.io/trojan-install)
```

![](/images/Trojan-go搭建/image-20210123221848951.png " ")

根据提示安装完毕后，可以使用`trojan`执行管理管理

![](/images/Trojan-go搭建/image-20210123222315968.png " ")

或者通过域名在web端进行管理，可以查看当前负载以及添加和用户管理（admin密码可以通过上一图的web管理进行重置）

![](/images/Trojan-go搭建/image-20210123223732652.png " ")

```shell
#卸载
source <(curl -sL https://git.io/trojan-install) --remove
```

## CND加速

**<font color=#DC143C>此步骤目的为降低网络延迟，不配置也不影响使用，不过墙裂推荐，速度快了不止一倍</font>**

如果要使用CDN加速，需要将trojan切换为trojan-go（脚本默认搭建为trojan），Trojan协议本身不带加密，安全性依赖外层的TLS。但流量一旦经过CDN，TLS对CDN是透明的。其服务提供者可以对TLS的明文内容进行审查。**如果你使用的是不可信任的CDN（任何在中国大陆注册备案的CDN服务均应被视为不可信任），请务必开启Shadowsocks AEAD对Webosocket流量进行加密，以避免遭到识别和审查。**

### cloudflare创建反代理加速

注册登录[cloudflare](https://www.cloudflare.com/zh-cn/)，根据提示拿到Cloudflare提供的DNS服务器

![](/images/Trojan-go搭建/image-20210124143858061.png " ")

回到域名提供商，将域名的DNS解析到Cloudflare

![](/images/Trojan-go搭建/image-20210124144436859.png " ")

配置完成后，可以在cloudflare首页看到域名是有效的，此时如果ping域名的话，是能看到域名解析的ip已经不是vps的ip了

![](/images/Trojan-go搭建/image-20210124151006831.png " ")

### 开启CDN，并设置CDN

点击DNS，代理状态为黄色，表示代理成功

![](/images/Trojan-go搭建/image-20210124153827226.png " ")

点击页面中的 SSL/TLS 进入如下界面并设置如图所示：（**重要**）

![](/images/Trojan-go搭建/image-20210124153922483.png " ")

### websocket开启

若是需要Trojan套用CDN，也就是必须开启 websocket

首先找到trojan-go的配置文件，然后进行备份

![](/images/Trojan-go搭建/image-20210124151711839.png " ")

在配置文件下面添加这2段，更多配置详情见[trojan-go官方文档](https://p4gefau1t.github.io/trojan-go/)

```shell
    "websocket": {
        "enabled": true,
        "path": "/DFE4545DFDED/",
        "host": "域名"
    }
```

`host`是主机名，一般填写域名。客户端`host`是可选的，填写你的域名。如果留空，将会使用`remote_addr`填充。

`path`指的是websocket所在的URL路径，必须以斜杠("/")开始。路径并无特别要求，满足URL基本格式即可，但要保证客户端和服务端的`path`一致。`path`应当选择较长的字符串，以避免遭到GFW直接的主动探测。

客户端的`host`将包含在Websocket的握手HTTP请求中，发送给CDN服务器，必须有效；服务端和客户端`path`必须一致，否则Websocket握手无法进行。

```shell
    "mux": {
        "enabled": true,
        "concurrency": 8,
        "idle_timeout": 60
    }
```

启用多路复用不会增加你的链路速度（甚至会有所减少），而且可能会增加服务器和客户端的计算负担。可以粗略地理解为，多路复用牺牲网络吞吐和CPU功耗，换取更低的延迟。在高并发的情景下，如浏览含有大量图片的网页时，或者发送大量UDP请求时，可以提升使用体验。

`concurrency`是每个TLS连接最多可以承载的TCP连接数。这个数值越大，每个TLS连接被复用的程度就更高，握手导致的延迟越低。但服务器和客户端的计算负担也会越大，这有可能使你的网络吞吐量降低。如果你的线路的TLS握手极端缓慢，你可以将这个数值设置为-1，Trojan-Go将只进行一次TLS握手，只使用唯一的一条TLS连接进行传输。

`idle_timeout`指的是每个TLS连接空闲多长时间后关闭。设置超时时间，**可能**有助于减少不必要的长连接存活确认(Keep Alive)流量传输引发GFW的探测。你可以将这个数值设置为-1，TLS连接在空闲时将被立即关闭。

### windows客户端配置

编辑连接，勾选Mux，Type选择ws，`host`和`Path`和服务端配置文件保持一致

![](/images/Trojan-go搭建/image-20210124160115672.png " ")



## windows配置

### Qv2ray及插件安装

[官网](https://github.com/Qv2ray/Qv2ray/releases)下载最新版本,以及trojan-go插件QvPlugin-Trojan-Go，插件放置在Qv2ray安装目录的plugins目录下，启动Qv2ray的时候会自动加载插件

![](/images/Trojan-go搭建/image-20210123224053302.png " ")

### trojan-go核心下载

[官网](https://github.com/p4gefau1t/trojan-go/releases)下载最新版本，为了方便管理，在Qv2ray安装目录下创建了个`trojan-go`目录，将文件放置在此处

![](/images/Trojan-go搭建/image-20210123224446229.png " ")

### v2ray-core下载

[官网](https://github.com/v2ray/v2ray-core/releases)下载最新版本，为了方便管理，在Qv2ray安装目录下创建了个`core`目录，将文件放置在此处

### Qv2ray配置

#### 插件配置

运行Qv2ray客户端，点击插件，选择插件QvPlugin-Trojan-Go，点击设定，点击Browser，选择上一步下载的trojan-go核心

![](/images/Trojan-go搭建/image-20210123224726095.png " ")

#### v2ray-core配置

点击首选项，选择内核设置，选择上一步下载的v2ray-core

![](/images/Trojan-go搭建/image-20210123231421131.png " ")

#### 新建连接

点击新建，配置如图

![](/images/Trojan-go搭建/image-20210123231733004.png " ")

### 验证

访问google，能正常访问，Qv2ray能看到访问的日志，搭建成功

![](/images/Trojan-go搭建/image-20210118231650953.png " ")  

## 安卓配置

下载Trojan安卓客户端（一般选择*-universal-release.apk）[https://github.com/trojan-gfw/igniter/releases](https://github.com/trojan-gfw/igniter/releases)，安装到手机即可。如果是使用trojan-go的建议使用trojan-go的安卓客户端，速度会比原版快很多。

![](/images/Trojan-go搭建/image-20210118231237972.png " ")  

## 相关软件

如果软件下载不方便可以从百度云下载，上传的软件不会再更新了，如果能在gitbub下载，尽量去gitbub下载新版

链接: [https://pan.baidu.com/s/1uKDzaBgt01iY4a15AQHwhg](https://pan.baidu.com/s/1uKDzaBgt01iY4a15AQHwhg) 提取码: tjhi 
