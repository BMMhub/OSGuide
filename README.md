# OpenWrt + Shadowsocks 一种局域网全局翻墙实践

## 0. 限定条件
1. 本文基于原版OpenWrt Chaos Calmer 15.05 x86 英文版写成，不确定在其他版本和平台上是否有效。
1. 需要自行准备Shadowsocks服务，并且已经具备一定的翻墙能力。
1. 本实践适合性能比较高的Shadowsocks服务，带宽和流量都有所保证。
1. 此次成文于2017.03.26，不保证今后是否有效或是否发生变动。
1. 为了最大的适用性，本文不会存在显式的下载链接。

## 1. 参考和原理

本文参考了飞宇博客的[这篇文章](https://cokebar.info/archives/962)和[这篇文章](https://cokebar.info/archives/664)，但实现原理不太一样，可以说是这两篇文章的结合。

在我看来，目前所谓翻墙，基本上可以认为是两个部分。第一部分是对域名的安全正确解析，第二部分是对ip地址的正确访问。

实际上纯粹的Shadowsocsk协议只能保证第二部分的达成，而关于dns的相关问题就需要通过某种“代理dns”或“无污染dns”来解决。

考虑到现有的Shadowsocks服务的带宽以及流量都能满足比较高的要求，兼顾本地网络访问性能，对于以上两部分的实现，有如下翻墙规则：

1. 对于[gfwlist](https://github.com/gfwlist/gfwlist)所列出的域名，一律使用“代理dns”进行解析；未列出的域名都使用正常默认dns进行解析。
2. 对解析出的ip地址进行地理位置判断，中国大陆ip不通过Shadowsocks访问，其他地区ip一律通过Shadowsocks访问。

对于第一条规则，可以通过`dnsmasq`服务对不同的域名制定相应解析规则，决定是通过普通dns解析还是通过"代理dns"解析。
对于第二条规则，可以直接在[OpenWrt LuCI for Shadowsocks-libev](https://github.com/shadowsocks/luci-app-shadowsocks)配套的配置界面中进行配置。

## 2. 一般实施步骤

假设现有一台干净安装OpenWrt Chaos Calmer 15.05 x86 的路由器。首先需要安全完整的`iptables`和`dnsmasq`。

- 登录路由器shell

- >opkg update

- >opkg install iptables-mod-nat-extra ipset

- 重启路由器，重新登录路由器shell

- >opkg update

- >opkg remove dnsmasq && opkg install dnsmasq-full

为了可以执行自动化的dnsmasq配置，需要安装`python`，跟着刚才的步骤，继续

- >opkg install python

接着安装[Shadowsocks-libev for OpenWrt](https://github.com/shadowsocks/openwrt-shadowsocks)和[OpenWrt LuCI for Shadowsocks-libev](https://github.com/shadowsocks/luci-app-shadowsocks)。

- 通过官方GitHub地址找到`Shadowsocks-libev for OpenWrt`的最新版安装包组合。下载`shadowsocks-libev`、 `libpcre`、`libsodium`、`libudns`等除了“server”以外所有安装包并把安装包推至路由器root目录下。

- 登录路由器shell，进入root目录。

- `opkg install`命令安装刚才下载的所有安装包，其中`shadowsocks-libev`最后安装。

- 通过官方GitHub地址找到`OpenWrt LuCI for Shadowsocks-libev`的安装包，下载不是"without-ipset"的版本并推至路由器root目录下。

- 登录路由器shell，进入root目录。

- `opkg install`命令安装刚才下载的安装包。

准备一份排除中国大陆ip地址的ip地址列表，保存在路由器`/etc/ignore.list`里。

-  登录路由器shell。

- >wget -O- 'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest' | awk -F\| '/CN\|ipv4/ { printf("%s/%d\n", $4, 32-log($5)/log(2)) }' > /etc/ignore.list

接着进行配置Shadowsocks，以实现翻墙第二部分功能（路由器）。

登录路由器luci界面，找到`Service`->`Shadowsocks`页面，进行Shadowsocks服务相关配置。值得注意的地方是在`Access Control`中，需要设置`Bypassed IP List`为`/etc/ignore.list`。

此时点击`Save and Apply`后Shadowsocks服务应该已经启动了。

接着实现翻墙的第一部分功能。对于“代理dns”，这里选择使用Shadowsocks的`Port Forward`功能。

- 登录路由器的luci界面，`Service`->`Shadowsocks`页面。

- 在`General Setting`中找到`Port Forward`功能并开启。设置`Local Port`为`5300`，`Destination`为`8.8.8.8:53`。 即是说开启了一个端口转发，将发送至本地5300端口的数据都通过Shadowsocks服务转发到谷歌的dns 8.8.8.8上。在本地实现了一个端口为5300的安全dns。

- 点击`Save and Apply`。

接着对dnsmasq的域名解析规则进行配置。

- 下载本git中的`config_dnsmaq.py`脚本。并推到路由器的root目录下。

- 登录路由器shell。

- 编辑`/etc/dnsmasq.conf`文件，加入最后一行`conf-dir=/etc/dnsmasq.d`。

- 新建`/etc/dnsmasq.d`文件夹。

- 进入root目录。

- >python config_dnsmaq.py

- 当出现`done!`字样，说明已经配置完成。

此时所有实施工作已经完成。

## 3. 其他需要说明的

### 1. 如何停止翻墙服务

总体来讲有点繁琐。

1. 首先通过luci界面将Shadowsocks服务全部关闭。

2. 登录路由器shell，删除`/etc/dnsmasq.d`目录下的所有问题。

3. >/etc/init.d/dnsmasq restart

### 2. 如何重新开启翻墙服务

1. 首先通过luci界面将Shadowsocks服务全部开启。

2. 登录路由器shell，在root目录下输入命令`python config_dnsmaq.py`。

### 3. 如何更新gfwlist域名

- 登录路由器shell，在root目录下输入命令`python config_dnsmaq.py`。

### 4. 如何更新中国ip地址

- 登录路由器shell。

- >wget -O- 'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest' | awk -F\| '/CN\|ipv4/ { printf("%s/%d\n", $4, 32-log($5)/log(2)) }' > /etc/ignore.list

- 登录luci界面，停止然后重新开启Shadowsocks相关服务。

### 5. 如何自定义ip地址通过规则

手动修改该 `/etc/ignore.list`或通过luci界面进行配置。


### 6. 如何自定义域名规则

`gfwlist`毕竟不是万能的，时效性也有一些问题。如果你指定其他域名使用“代理dns”进行查询的话，可以按照以下步骤进行。

- 登录路由器shell。

- 在root目录下新建`custom.list`文件，并把需要的域名列在上面。

- >python config_dnsmaq.py

### 7. 如何指定其他的“代理dns”

本文通过Port Forward功能实现了“代理dns”，当然如果你有其他方式比如DNSCrypt或者非标准dns端口的话也可以使用，按照如下步骤进行设置。

- 登录路由器shell。
- 编辑`config_dnsmaq.py`文件。
- 将`mydnsip`和`mydnsport`变量修改成你需要的dns ip地址和端口即可。

值得注意的是，如果你选用了不依赖于Shadowsocks服务的“代理dns”方案，那么在停止翻墙服务的时候就不需要执行第二三步，在重新开启翻墙服务的时候不需要执行第二步。

