import random

from xingchen import (
    ApiClient,
    CharacterApiSub,
    CharacterKey,
    CharacterQueryDTO,
    CharacterQueryWhere,
    CharacterUpdateDTO,
    ChatApiSub,
    ChatContext,
    ChatHistoryQueryDTO,
    ChatHistoryQueryWhere,
    ChatMessageApiSub,
    ChatReqParams,
    Configuration,
    Message,
    ModelParameters,
    ResetChatHistoryRequest,
    UserProfile,
)

from libs.bvcutils import get_patient_info
from libs.bvcconst import SYSTEM_PROMPT

class XingChen:
    def __init__(self, api_key):
        self.configuration = Configuration(host="https://nlp.aliyuncs.com")
        # xingchen QPS=1 APIMAX=10
        self.configuration.access_token = api_key
        with ApiClient(self.configuration) as api_client:
            self.chat_api = ChatApiSub(api_client)
            self.character_api = CharacterApiSub(api_client)
            self.chat_message_api = ChatMessageApiSub(api_client)

    def chat(self, doctor, patient) -> str:
        # info = get_patient_info(patient)
        # content = "\n【你的人设】\n" + info + SYSTEM_PROMPT
        # print(content)
        # system_prompt = [{'role':'system','content':content}]
        content = patient.messages[0]['content']
        messages = patient.messages[1:]
        chat_param = ChatReqParams(
            bot_profile=CharacterKey(
                # name="患者",
                content=content,
                # traits="强制要求"
            ),
            model_parameters=ModelParameters(
                seed=1683806810,
                top_p=0.95,   
                temperature=0.92,
                incrementalOutput=False
            ),
            messages=messages,
            context=ChatContext(use_chat_history=False),
            user_profile=UserProfile(user_id=doctor.id),
        )
        # chat_param = ChatReqParams(
        #     bot_profile=CharacterKey(character_id=patient.id),
        #     model_parameters=ModelParameters(
        #         seed=random.getrandbits(32), incrementalOutput=False
        #     ),
        #     messages=[Message(role="user", content=patient.messages[-1]["content"])],
        #     context=ChatContext(use_chat_history=True),
        #     user_profile=UserProfile(user_id=doctor.id),
        # )
        try:
            response = self.chat_api.chat(chat_param).to_dict()
            if response["success"]:
                return response["data"]["choices"][0]["messages"][0]["content"]
            else:
                return (
                    f"( 似乎自己在思索什么，嘴里反复说着数字 ~ {response['code']} ~ )"
                )
        except Exception as exception:
            return f"( 脑子坏掉了，等会再问我吧 ~ 原因是: {exception})"

    def character_create(self, patient):
        pass

    def character_delete(self, patient):
        pass

    def character_update(self, character) -> bool:
        body = CharacterUpdateDTO.from_dict(character)
        result = self.character_api.update(character_update_dto=body)
        return result.to_dict()["data"]

    def character_details(self, patient) -> dict:
        # detail = self.character_api.character_details(character_id=patient.id)
        detail = self.character_api.character_details(character_id=patient)
        return detail.data.to_dict()

    def character_search(self, scope="my") -> list:
        body = CharacterQueryDTO(
            where=CharacterQueryWhere(scope=scope), pageNum=1, pageSize=100
        )
        result = self.character_api.search(character_query_dto=body)
        return result.data.to_dict()["list"]

    def get_chat_histories(self, doctor, patient) -> list:
        body = ChatHistoryQueryDTO(
            where=ChatHistoryQueryWhere(characterId=patient.id, bizUserId=doctor.id),
            orderBy=["gmtCreate desc"],
            pageNum=1,
            pageSize=10,
        )
        result = self.chat_message_api.chat_histories(chat_history_query_dto=body)
        return result.data.to_dict()

    def reset_chat_history(self, doctor, patient) -> bool:
        body = ResetChatHistoryRequest(characterId=patient.id, userId=doctor.id)
        result = self.chat_message_api.reset_chat_history(request=body)
        return result.data
