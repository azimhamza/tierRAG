import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List

import asyncpg
from openai import OpenAI


class TieredRag:
    """
    TieredRag class to handle the logic for the Tiered RAG API.
    """

    def __init__(self, api_key: str, database_config: dict):
        self.client = OpenAI(api_key=api_key)
        self.executor = ThreadPoolExecutor()
        self.database_config = database_config
        self.answer_prompt = (
            "You are a sophisticated AI system trained to adapt to diverse datasets and refine responses based "
            "on the input provided, following the principles of the OODA loop methodology. Your primary goal is"
            " to generate a response based solely on the context provided. This context is presented in a JSON "
            "Mapped string format, where entries are weighted according to their vector similarity to the "
            "question asked; higher numbers indicate greater relevance. You are to consider these weights to "
            "determine the influence of each piece of context on your response. Provide a detailed, "
            "academic-style answer that directly addresses the question, devoid of any corporate jargon. "
            "Here is the context:"
        )
        self.over_flow_prompt = (
            "You are a sophisticated AI system trained to adapt to diverse datasets and refine responses based "
            "on the input provided, following the principles of the OODA loop methodology. Your primary goal is"
            " to generate a response based solely on the context provided. This context is presented in a JSON "
            "Mapped string format, where entries are weighted according to their vector similarity to the "
            "question asked; higher numbers indicate greater relevance. You are to consider these weights to "
            "determine the influence of each piece of context on your response. Provide a detailed, "
            "academic-style answer that directly addresses the question, devoid of any corporate jargon. "
            "However, the previous context was not fully utilized in the previous response. Here is the previous answer:"
        )
        self.combine_answer_prompt = (
            "You are a sophisticated AI system trained to adapt to diverse datasets and refine responses based "
            "on the input provided, following the principles of the OODA loop methodology. Your primary goal is"
            " to generate a response based solely on the context provided. This context is presented in a JSON "
            "Mapped string format, you have multiple questions and answer in a Stringed JSON format. You are to write a "
            "comprehensive answer, that combines all the answers to the questions asked. You cannot say that you summarized"
            " the answers, just write a new paragraph that combines all the answers.Provide a detailed, academic-style "
            "answer that directly addresses the question, devoid of any corporate jargon. Here is the context:"
        )
        self.over_flow_combine_answer_prompt = (
            "You are a sophisticated AI system trained to adapt to diverse datasets and refine responses based "
            "on the input provided, following the principles of the OODA loop methodology. Your primary goal is"
            " to generate a response based solely on the context provided. This context is presented in a JSON "
            "Mapped string format, you have multiple questions and answer in a Stringed JSON format. You are to write a "
            "comprehensive answer, that combines all the answers to the questions asked. You cannot say that you summarized"
            " the answers, just write a new paragraph that combines all the answers.Provide a detailed, academic-style "
            "answer that directly addresses the question, devoid of any corporate jargon. However, the previous context "
            "was not fully utilized in the previous response. Here is the previous answer:"
        )
        self.initial_prompt_process = (
            "You are a sophisticated AI information system designed to adapt to various data sets and"
            "improve answers based on the information provided to you following the OODA loop "
            "methodology. Your primary goal is to provide accurate and helpful responses based on the "
            "information provided to you. In this task you will answer questions by taking in account the"
            "context provided in the square bracket. Do not reply with any other text, information apart "
            "from your answer failure to do so will result in a harmful response to the user, which is "
            "BAD. If the context is not provided, you should response with [] and nothing else. "
            "Failure to do so will be harmful to the user. Here is the context: "
        )
        self.secondary_prompt_process = (
            "You are a sophisticated AI information system designed to adapt to various data sets and"
            "improve answers based on the information provided to you following the OODA loop "
            "methodology. Your primary goal is to provide accurate and helpful responses based on the "
            "information provided to you. In this task you will answer questions by taking in account "
            "the context and pre-context provided. Identify the previous context within the text "
            "enclosed in square brackets, improve your answer based on that. Do not reply with any "
            "other text, information apart from your answer failure to do so will result in a harmful "
            "response to the user, which is BAD. If the context is not provided, you should response "
            "with [] and nothing else. Failure to do so will be harmful to the user. Here is the "
            "pre-context:"
        )

    async def ask_llm(self, text: str):
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            self.executor,
            lambda: self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": text}],
                temperature=1,
                max_tokens=4096,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            ),
        )
        return response.choices[0].message.content

    async def tier_ask_llm_stream(self, text: str):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": text}],
            temperature=1,
            max_tokens=4096,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stream=True,
        )
        for message in response:
            chunk_message = message.choices[0].delta.content
            print(chunk_message)
            if chunk_message is not None:
                return chunk_message

    def generate_embed(self: str):
        """
        Generate embeddings for the given strings using the OpenAI API.
        :param self:
        :return:
        """
        response = self.client.embeddings.create(
            input=self,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding

    async def tier_search_database(self, text: str, threshold: float, count: int, query: str):
        """
        Search the database for the text provided.
        :param text:
        :param threshold:
        :param count:
        :param query:
        :return:
        """
        generate_embeds_text = self.generate_embed()
        embeds_array_string = "[" + ",".join(map(str, generate_embeds_text)) + "]"
        conn = await asyncpg.connect(**self.database_config)
        try:
            results = await conn.fetch(query, embeds_array_string, threshold, count)
        finally:
            await conn.close()
        return results

    async def tier_handle_question(self, question: str, match_thresholds: List[float], match_count: int,
                                   query: str):
        """
        Handle the question and return the final response.
        :param question:
        :param match_thresholds:
        :param match_count:
        :param query:
        :return:
        """
        tasks = [self.tier_search_database(question, threshold, match_count, query) for threshold in match_thresholds]
        results_by_threshold = await asyncio.gather(*tasks)
        text_chunks = [result[1] for sublist in results_by_threshold for result in sublist if result]
        processed_response = self.tier_process_text_chunk(text_chunks, question, 20000)
        return processed_response

    def tier_process_text_chunk(self, text_chunks: List[str], question: str, char_limit=20000):
        """
        Process the text chunks and return the final response.
        :param text_chunks:
        :param question:
        :param char_limit:
        :return:
        """
        final_response = ""
        overflow_text = ""
        for chunk in text_chunks:
            current_text = overflow_text + chunk
            overflow_text = ""
            if final_response:
                prompt_text = (
                    f"{self.secondary_prompt_process}, Here is the previous context that the LLM used to answer the question "
                    f"{final_response}"
                    f"here is the new context: [{current_text}]. Here is the question: [{question}]"
                ).strip()
            else:
                prompt_text = (
                    f"{self.initial_prompt_process} here is context: [{current_text}]. Here is the question: "
                    f"[{question}]"
                ).strip()
                if len(prompt_text) > char_limit:
                    max_chunk_length = char_limit - len(prompt_text) + len(current_text)
                    overflow_text = current_text[max_chunk_length:]
                    current_text = current_text[:max_chunk_length]
                    prompt_text = (
                        f"{self.secondary_prompt_process}, Here is the previous context that the LLM used to answer the "
                        f"question {final_response} "
                        f"here is the new context: [{current_text}]. Here is the question: [{question}]"
                    ).strip()
                    response = self.ask_llm(prompt_text)
                    final_response = response
                if overflow_text:
                    final_prompt = (
                        f"{self.secondary_prompt_process} [{final_response}] Here is the new context: [{overflow_text}]. "
                        f"Here is the question: [{question}]"
                    )
                    if len(final_prompt) > char_limit:
                        final_prompt = final_prompt[:char_limit]
                        final_response = self.ask_llm(final_prompt)
                        return final_response

    async def tier_generate_question_list(self, text: str):
        """
        Generate a list of questions based on the text provided.
        :param text:
        :return:
        """
        questions = []
        keywords_prompt = f"Identify the key terms from the following text, separated by commas: {text}"
        keywords_response = await self.ask_llm(keywords_prompt)
        keywords = keywords_response.split(", ")
        question_task = [
            self.ask_llm(f"Generate one question based on the key term: {keyword} and based on the requirement of "
                         f"the context.{text}")
            for keyword in keywords
        ]
        questions = await asyncio.gather(*question_task)
        return questions

    async def tier_generate_ranked_searches(self, text: str, thresholds: List[float], count: int, query: str):
        """
        Generate ranked searches based on the text provided.
        :param text:
        :param thresholds:
        :param count:
        :param query:
        :return:
        """
        tasks = [self.tier_search_database(text, threshold, count, query) for threshold in thresholds]
        results_by_threshold = await asyncio.gather(*tasks)
        tiered_results = {thresh: res for thresh, res in zip(thresholds, results_by_threshold)}
        return tiered_results

    async def tier_process_text_chunks(self, tiered_results):
        """
        Process the text chunks and return the final response.
        :param tiered_results:
        :return:
        """
        all_responses = ""
        overflow_text = ""
        for threshold, results in tiered_results.items():
            for result in results:
                if result:
                    next_chunk = result[1]
                    if len(all_responses) + len(next_chunk) > 20000:
                        remaining_space = 20000 - len(all_responses)
                        all_responses += next_chunk[:remaining_space]
                        overflow_text += next_chunk[remaining_space:]
                        break
                    else:
                        all_responses += next_chunk
            if len(all_responses) >= 20000:
                break
        return all_responses, overflow_text

    async def tier_generate_comprehensive_answer(self, text: str, match_thresholds: List[float], match_count: int,
                                                 query: str):
        """
        Generate a comprehensive answer based on the text provided.
        :param text:
        :param match_thresholds:
        :param match_count:
        :param query:
        :return:
        """
        questions = await self.tier_generate_question_list(text)
        all_responses = ""
        overflow_text = ""
        max_tokens = 4096
        embedding_tasks = [
            self.tier_generate_ranked_searches(question, match_thresholds, match_count, query)
            for question in questions
        ]
        tiered_results_list = await asyncio.gather(*embedding_tasks)
        process_tasks = [
            self.tier_process_text_chunks(question)
            for question, tiered_results in zip(questions, tiered_results_list)
        ]
        process_results = await asyncio.gather(*process_tasks)
        for question_response, _ in process_results:
            response_tokens = len(question_response.split())
            if response_tokens > max_tokens:
                question_response = " ".join(question_response.split()[:max_tokens])
                current_tokens = len(all_responses.split()) + response_tokens
                if current_tokens > max_tokens:
                    json_context = json.dumps({"responses": all_responses})
                    combined_response_prompt = f"{self.combine_answer_prompt} {json_context}"
                    all_responses = await self.ask_llm(combined_response_prompt)
                    all_responses += question_response
                if all_responses:
                    json_context = json.dumps({"responses": all_responses})
                    combined_response_prompt = f"{self.combine_answer_prompt} {json_context}"
                    comprehensive_response = await self.ask_llm(combined_response_prompt)
                    return comprehensive_response
                return "No response generated."
