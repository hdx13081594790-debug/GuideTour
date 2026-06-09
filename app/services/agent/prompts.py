# Prompt 常量占位。
#
# 早期规则 Agent/未来 LangGraph 节点可复用这里的提示词。
# 当前真正的 DeepSeek 结构化决策 prompt 在 deepseek_client.py 中，
# 因为它需要动态拼接 POI 列表和请求上下文。

INTENT_PROMPT = "识别游客意图：导航、附近讲解、历史问答、拍照、停止导航或未知。"
ANSWER_PROMPT = "基于工具结果生成简洁、可朗读、不可编造历史细节的中文导览回答。"
