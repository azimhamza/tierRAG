# TieredRag Library

The TieredRag library is a Python implementation of a tiered retrieval-augmented generation (RAG) system. It leverages the power of vector similarity search and the OpenAI GPT-3.5-turbo model to generate comprehensive and accurate responses to user queries based on a given dataset.

## Motivation

The motivation behind the TieredRag library is to provide a cost-effective solution for generating high-quality responses using a cheaper language model while potentially outperforming more expensive models. By employing a tiered approach and utilizing vector similarity search, the library aims to improve the model's understanding of ranked items, enhance its memory recall, and reduce the time required for generating responses.

## How It Works

The TieredRag library follows a multi-step process to generate responses:

1. **Question Generation**: Given a text input, the library generates a list of relevant questions using the `tier_generate_question_list` method. It identifies key terms from the input text and generates questions based on those terms.

2. **Tiered Search**: For each generated question, the library performs a tiered search using the `tier_generate_ranked_searches` method. It searches the database at different similarity thresholds to retrieve relevant context chunks. The search results are ranked based on their vector similarity to the question, with higher similarity scores indicating greater relevance.

3. **Context Processing**: The retrieved context chunks are processed using the `tier_process_text_chunks` method. It combines the context chunks into a single response, taking into account the maximum character limit. If the combined response exceeds the limit, it is truncated and the remaining context is stored as overflow text.

4. **Response Generation**: The processed context is used to generate a comprehensive response using the `tier_generate_comprehensive_answer` method. It iterates over the generated questions and their corresponding ranked search results. For each question, it generates a response based on the processed context. If the response exceeds the maximum token limit, it is truncated and added to the overall response.

5. **Combining Responses**: If multiple responses are generated for different questions, they are combined into a single comprehensive response using the `combine_answer_prompt`. The library uses the GPT-3.5-turbo model to generate a coherent and unified response based on the combined context.

## Improving Model Understanding and Memory Recall

The TieredRag library improves the model's understanding of ranked items by utilizing vector similarity search. By ranking the context chunks based on their similarity to the question, the model can prioritize the most relevant information when generating responses. This approach helps the model focus on the key aspects of the question and retrieve the most pertinent context.

Furthermore, the tiered search approach allows the model to access a wider range of relevant information. By searching at different similarity thresholds, the library can retrieve context chunks that may not be an exact match but still provide valuable insights. This enhances the model's memory recall and enables it to generate more comprehensive responses.

## Reducing Response Time

The TieredRag library employs several techniques to reduce the time required for generating responses:

1. **Asynchronous Processing**: The library utilizes asynchronous programming with the `asyncio` library to perform multiple tasks concurrently. This allows for efficient processing of questions, database searches, and response generation.

2. **Tiered Search**: By performing a tiered search at different similarity thresholds, the library can quickly retrieve the most relevant context chunks without exhaustively searching the entire database. This reduces the search time and improves response generation speed.

3. **Context Truncation**: If the retrieved context exceeds the maximum character limit, the library truncates it to fit within the limit. This prevents the model from processing unnecessarily large amounts of text and helps reduce the response generation time.

4. **Caching**: The library can be extended to incorporate caching mechanisms to store frequently accessed context chunks or generated responses. Caching can significantly reduce the response time for recurring queries or similar questions.

## Conclusion

The TieredRag library provides a powerful and efficient solution for generating comprehensive responses using a cost-effective language model. By leveraging vector similarity search, tiered retrieval, and asynchronous processing, the library improves the model's understanding of ranked items, enhances its memory recall, and reduces the response generation time. This approach has the potential to outperform more expensive models while maintaining high-quality output.

The library can be easily integrated into existing applications or scripts, making it a valuable tool for various natural language processing tasks. With its modular design and customizable prompts, the TieredRag library offers flexibility and extensibility to adapt to different use cases and datasets.


### There is significant places to improve espically with reducing timing of generation to more better caching of responses.
