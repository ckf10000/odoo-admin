# -*- coding: utf-8 -*-
"""公共 Pydantic Schema — 供所有 API 模块和 Swagger 共享"""
from typing import Optional
from pydantic import BaseModel, Field


class ApiHeader(BaseModel):
    """API 请求头 — 签名认证 + 设备信息"""
    # 必填签名参数
    clientId: Optional[str] = Field(default="", description="客户端ID，用于查找 appSecret")
    X_Token: str = Field(default="", alias="X-Token", description="登录后的 access_token，登录/刷新时传空串")
    X_Timestamp: str = Field(..., alias="X-Timestamp", min_length=1, description="毫秒时间戳")
    X_Nonce: str = Field(..., alias="X-Nonce", min_length=1, description="随机 UUID，防重放")
    X_Sign: str = Field(..., alias="X-Sign", min_length=1, description="MD5(timestamp+nonce+token+bodyJSON+appSecret)")

    # 可选设备信息
    platformType: Optional[str] = Field(default=None, description="android / ios / harmonyos")
    platformVersion: Optional[str] = Field(default=None, description="系统版本")
    deviceBrand: Optional[str] = Field(default=None, description="设备品牌")
    deviceModel: Optional[str] = Field(default=None, description="设备型号")
    deviceId: Optional[str] = Field(default=None, description="设备唯一标识")
    rooted: Optional[bool] = Field(default=None, description="是否 root / 越狱")
    sdkVersion: Optional[str] = Field(default=None, description="SDK 版本")
    networkType: Optional[str] = Field(default=None, description="wifi / 4g / 5g")
    screenWidth: Optional[int] = Field(default=None, description="屏幕宽度")
    screenHeight: Optional[int] = Field(default=None, description="屏幕高度")
    screenDensity: Optional[float] = Field(default=None, description="屏幕密度")
    language: Optional[str] = Field(default=None, description="语言")
    timezone: Optional[str] = Field(default=None, description="时区")
    imei: Optional[str] = Field(default=None, description="IMEI")
    oaid: Optional[str] = Field(default=None, description="OAID")
    appVersion: Optional[str] = Field(default=None, description="App 版本")
    appBuild: Optional[str] = Field(default=None, description="构建号")
    appChannel: Optional[str] = Field(default=None, description="渠道")
    appBuildType: Optional[str] = Field(default=None, description="debug / release")
