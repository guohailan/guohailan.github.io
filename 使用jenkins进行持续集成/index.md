# 使用Jenkins进行持续集成


使用Jenkins进行持续集成，案例在虚拟机上进行搭建，本文主要介绍环境搭建以及配置部分。
<!--more-->
## 准备工作
机器要求：
* 256 MB 内存，建议大于 512 MB
* 10 GB 的硬盘空间（用于 Jenkins 和 Docker 镜像）

需要安装以下软件
* Java 8 ( JRE 或者 JDK 都可以)

首先从[官网](https://www.jenkins.io/zh/)上下载Jenkins安装包，为方便使用这里我直接下载了war包进行安装
```bash
wget http://mirrors.jenkins.io/war-stable/latest/jenkins.war
```
从国内源下载JDK 8,并且设置JAVA_HOME
```bash
wget https://repo.huaweicloud.com/java/jdk/8u201-b09/jdk-8u201-linux-x64.tar.gz  # 下载JDK安装包
echo 'export JAVA_HOME=/usr/java/jdk1.8.0_201
export PATH=$JAVA_HOME/bin:$PATH' >>/etc/profile  # 配置java环境变量
source /etc/profile  # 使配置的环境变量生效
```
`java -version`查看java版本,如果出现下图结果，表示JDK安装成功
![](/images/使用Jenkins进行持续集成/java_home.png " ")

## 使用Jenkins
执行`java -jar jenkins.war --httpPort=8080`启动jenkins，打开浏览器进入链接`http://localhost:8080`,访问jenkis
### 解锁Jenkins
第一次访问新的Jenkins实例时，系统会要求使用自动生成的密码对其进行解锁。
![](/images/使用Jenkins进行持续集成/release.png " ")
从Jenkins控制台日志输出中，复制自动生成的字母数字密码（在两组星号之间）
![](/images/使用Jenkins进行持续集成/password.png " ")
### 插件初始化
在解锁Jenkins页面上，将此密码粘贴到管理员密码字段中，然后单击继续,此时会进入插件安装界面,根据需要进行选择，这里我直接选择了自定义安装，暂时不安装任何插件，因为没有更改源，安装很慢
- 安装建议的插件 - 安装推荐的一组插件，这些插件基于最常见的用例.
- 选择要安装的插件 - 选择安装的插件集。当你第一次访问插件选择页面时，默认选择建议的插件。

![](/images/使用Jenkins进行持续集成/plugin.png " ")
插件下载完成后即可进入主页
![](/images/使用Jenkins进行持续集成/home_page.png " ")

### 主从搭建
先点击Manage Jenkins，然后点击Manage Nodes and Clouds
![](/images/使用Jenkins进行持续集成/node.png " ")
点击新建节点
![](/images/使用Jenkins进行持续集成/slave.png " ")
填写slave相关信息,点击保存
![](/images/使用Jenkins进行持续集成/slave_info.png " ")
在Configure Global Security中启用代理Java Web Start Agent Protocol/4 (TLS 加密)配置
![](/images/使用Jenkins进行持续集成/agent.png " ")
然后根据提示，将agent.jar拷贝到slave节点目录，然后根据提示的命令运行slave
![](/images/使用Jenkins进行持续集成/run_slave.png " ")
此时可以看到slave已经上线
![](/images/使用Jenkins进行持续集成/slave1.png " ")
### 用户权限配置
在一个部门内部，可能存在多个运维人员，而这些运维人员往往负责不同的项目，但是有可能他们用的又是同一个 Jenkins 的不同用户。那么我们就希望实现一个需求，能够不同的用户登录 Jenkins 以后看到不同的项目。由于jenkins默认的权限控制太过简陋，因此我们引入新的插件`Role-based Authorization Strategy`
#### 插件安装
首先因国内直连jenkens的插件中心速度很慢，因此先修改源站为清华大学地址`https://mirrors.tuna.tsinghua.edu.cn/jenkins/updates/update-center.json`
![](/images/使用Jenkins进行持续集成/qinghua.png " ")
然后搜索插件名进行安装
![](/images/使用Jenkins进行持续集成/plugin1.png " ")
### 权限配置
重启Jenkins以后，再度打开Configure Global Security会发现多了我们刚刚插件的选项，选择Role-Based Strategy，点击保存
![](/images/使用Jenkins进行持续集成/role.png " ")
这时在Manage Jenkins就会多出一个选项，Manage and Assign Roles
![](/images/使用Jenkins进行持续集成/manage_role.png " ")
在Manage Roles进行角色以及相关权限添加，有Global roles、Item roles以及Node roles可以分别进行配置
![](/images/使用Jenkins进行持续集成/global.png " ")
然后点击Assign Roles，进行相关用户的角色授予
![](/images/使用Jenkins进行持续集成/assign_roles.png " ")
### 创建JOB
点击新建job，创建一个Freestyle project的JOB
![](/images/使用Jenkins进行持续集成/myjob.png " ")
点击新创建的JOB进行配置，源码管理选择GIT(需要提前安装git插件才会出来这个选项，填入git库地址，以及相关账号及密码)
![](/images/使用Jenkins进行持续集成/git.png " ")
定时触发器可根据实际情况进行选择，然后配置构建步骤点击保存即可，我本地是部署nginx静态页面，因此直接执行shell命令进行部署
![](/images/使用Jenkins进行持续集成/deploy.png " ")
### 触发构建
点击立即构建，即可触发构建任务，本次部署为和jenkins同一台机器上的nginx静态页面
![](/images/使用Jenkins进行持续集成/build.png " ")
点击控制台输出，可以查看构建过程中的具日志
![](/images/使用Jenkins进行持续集成/log.png " ")
