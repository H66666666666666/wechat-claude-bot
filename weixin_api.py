"""微信API客户端 - 基于openclaw-weixin协议"""

import time
import logging
import requests
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class WeixinMessage:
    """微信消息"""

    def __init__(self, data: Dict[str, Any]):
        self.seq = data.get("seq")
        self.message_id = data.get("message_id")
        self.from_user_id = data.get("from_user_id", "")
        self.to_user_id = data.get("to_user_id", "")
        self.create_time_ms = data.get("create_time_ms", 0)
        self.session_id = data.get("session_id", "")
        self.message_type = data.get("message_type", 0)  # 1=USER, 2=BOT
        self.message_state = data.get("message_state", 0)
        self.item_list = data.get("item_list", [])
        self.context_token = data.get("context_token", "")
        self._raw = data

    @property
    def text(self) -> str:
        """获取文本内容"""
        for item in self.item_list:
            if item.get("type") == 1:  # TEXT
                text_item = item.get("text_item", {})
                return text_item.get("text", "")
        return ""

    @property
    def is_user_message(self) -> bool:
        return self.message_type == 1

    @property
    def is_bot_message(self) -> bool:
        return self.message_type == 2


class WeixinAPI:
    """微信API客户端"""

    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/") + "/"
        self.token = token
        self.get_updates_buf = ""
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
        })
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送POST请求"""
        url = self.base_url + endpoint
        try:
            resp = self.session.post(url, json=data, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"POST {endpoint} failed: {e}")
            raise

    def get_updates(self, timeout_ms: int = 35000) -> List[WeixinMessage]:
        """获取新消息（长轮询）"""
        data = {
            "get_updates_buf": self.get_updates_buf,
        }

        try:
            resp = self._post("ilink/bot/getupdates", data)

            # 检查是否有错误
            if "errcode" in resp:
                errcode = resp.get("errcode", 0)
                errmsg = resp.get("errmsg", "")
                # -14 = 会话超时，正常情况
                if errcode == -14:
                    logger.debug("Session timeout, retrying...")
                    return []
                logger.error(f"getUpdates error: {errcode} {errmsg}")
                return []

            # 更新同步游标
            new_buf = resp.get("get_updates_buf", "")
            if new_buf:
                self.get_updates_buf = new_buf

            msgs = resp.get("msgs", [])
            return [WeixinMessage(m) for m in msgs]

        except Exception as e:
            logger.error(f"getUpdates failed: {e}")
            return []

    def send_message(self, to_user_id: str, text: str, context_token: str = "") -> bool:
        """发送文本消息"""
        data = {
            "msg": {
                "to_user_id": to_user_id,
                "context_token": context_token,
                "item_list": [
                    {
                        "type": 1,  # TEXT
                        "text_item": {"text": text}
                    }
                ]
            }
        }

        try:
            resp = self._post("ilink/bot/sendmessage", data)
            return True
        except Exception as e:
            logger.error(f"sendMessage failed: {e}")
            return False

    def send_typing(self, ilink_user_id: str, typing_ticket: str, status: int = 1) -> bool:
        """发送输入状态"""
        data = {
            "ilink_user_id": ilink_user_id,
            "typing_ticket": typing_ticket,
            "status": status,  # 1=typing, 2=cancel
        }

        try:
            resp = self._post("ilink/bot/sendtyping", data)
            return resp.get("ret", -1) == 0
        except Exception as e:
            logger.error(f"sendTyping failed: {e}")
            return False

    def get_config(self, ilink_user_id: str, context_token: str = "") -> Dict[str, Any]:
        """获取配置（包含typing_ticket）"""
        data = {
            "ilink_user_id": ilink_user_id,
            "context_token": context_token,
        }

        try:
            return self._post("ilink/bot/getconfig", data)
        except Exception as e:
            logger.error(f"getConfig failed: {e}")
            return {}

    def notify_start(self) -> bool:
        """通知服务端启动"""
        try:
            resp = self._post("ilink/bot/msg/notifystart", {})
            return resp.get("ret", -1) == 0
        except Exception as e:
            logger.error(f"notifyStart failed: {e}")
            return False

    def notify_stop(self) -> bool:
        """通知服务端停止"""
        try:
            resp = self._post("ilink/bot/msg/notifystop", {})
            return resp.get("ret", -1) == 0
        except Exception as e:
            logger.error(f"notifyStop failed: {e}")
            return False
