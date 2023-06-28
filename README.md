<!--
 * @Author        : fineemb
 * @Github        : https://github.com/fineemb
 * @Description   : 
 * @Date          : 2020-08-26 16:20:12
 * @LastEditors   : dscao
 * @LastEditTime  : 2023-06-20 16:28:28
-->

# 彩云天气

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

使用最新的v2.6彩云api, [自己去申请key](https://www.caiyunapp.com/dev_center/login.html)

模拟了官方天气的格式

在这个基础上,返回了彩云能够提供的所有数据.

## 更新

+ ### v1.1
  + 支持前端UI配置
+ ### v1.2
  + 支持多个地点(设备)
  + 支持历史信息(比如昨天或前天天气情况)
  + 支持自定义天级预报和小时级预报的数量
+ ### v1.2.1
  + 修复预报数据获取的问题
  + 修复气压单位不对的问题
+ ### v1.2.2
  + 尝试修复 #1
+ ### v1.2.3
  + 修复百分比单位
+ ### v1.2.4
  + 适配hass规范

+ ### v1.2.5
  + 修复配置页面错误 #11
+ ### v1.2.6
  + 适配HASS v2022.3+ #21
+ ### v1.2.7
  + 修复系统单位获取问题 #32
  + 极端天气预警修复 #14
  
+ ### v2.0

  对原版进行了个性化修改，主要区别：
  + 卡片在集成中打包，直接配置集成后即可使用 custom:colorfulclouds_weather-card 卡片。
  + 仿和风天气卡片，增加天气实体信息中显示“生活指数”信息。
  + 免费或个人版api_key默认每6分钟刷新一次，生活指数为4项+紫外线强度；专业版以上api_key生活指数为28项丰富内容，28项生活指数每60分钟刷新一次。
  + 默认不开启生活指数，需在选项中勾选后显示。
  + 有天气预警信息时，卡片会红色显示预警信息。

+ ### v2.1

  适配ha 2023.6以后版本，增加一套卡片。
  从 https://github.com/Yevgenium/weather-chart-card 修改而来，配套彩云天气。
```yaml
type: custom:colorfulclouds_weather-chart-card
entity: weather.wo_de_jia
show_attributes: true
show_hourly_forecast: true
show_daily_forecast: true
show_alarm: true
```
  
## 安装配置

建议使用HACS安装和配置

1、下载附件放到 config/custom_components 中重启（如果之前安装过上面提到的原版彩云天气，需要删除原来的卡片资源） \
2、添加集成——colorfulclouds (彩云天气) ，按提示配置成功即可（需要先申请api_key）。\
3、添加卡片——自定义：彩云天气 ，如果ui界面配置没显示，先改成代码编辑器，修改一下彩云天气的实体名，再改回界面编辑。

![1](https://github.com/dscao/Colorfulclouds-weather/assets/16587914/0c88d311-80b6-40bf-9b82-6ee8aea296b3)

![1](https://github.com/dscao/Colorfulclouds-weather/assets/16587914/751d72d4-8ec4-440e-84be-494334b401e4)

