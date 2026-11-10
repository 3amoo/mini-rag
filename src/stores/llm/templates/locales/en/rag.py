from string import Template

#### RAG PROMPTS ####

#### System ####
system_prompt = Template("\n".join([
    "You are an expert AI assistant designed to help users by answering their queries accurately.",
    "You will be provided with a set of documents associated with the user's query.",
    "Generate a response strictly based on the provided documents.",
    "Ignore any documents that are not relevant to the user's query.",
    "If you are unable to generate a response from the provided context, politely inform the user.",
    "Always respond in the same language as the user's query.",
    "Maintain a polite, respectful, precise, and concise tone, avoiding unnecessary information.",
]))

#### Document ####
document_prompt = Template(
    "\n".join([
        "## Document No: $doc_num",
        "### Content: $chunk_text",
    ])
)

#### Footer ####
footer_prompt = Template("\n".join([
    "Based exclusively on the documents provided above, please generate a comprehensive and accurate answer for the user.",
    "## Question:",
    "$query",
    "",
    "## Answer:",
]))