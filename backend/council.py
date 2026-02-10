"""3-stage LLM Council orchestration."""

from typing import List, Dict, Any, Tuple
from openrouter import query_models_parallel, query_model
from config import COUNCIL_MODELS, CHAIRMAN_MODEL, STAGE2_MODELS, TITLE_MODEL


async def stage1_collect_responses(
    user_query: str, 
    history: List[Dict[str, Any]] = None,
    attachments: List[Dict[str, Any]] = None,
    is_lab_mode: bool = False
) -> List[Dict[str, Any]]:
    """
    Stage 1: Collect individual responses or prompt variations.

    Args:
        user_query: The user's question
        history: Optional conversation history
        attachments: Optional list of file attachments

    Returns:
        List of dicts with 'model' and 'response' keys
    """
    # Format messages for models
    messages = []
    if history:
        for msg in history:
            if msg['role'] == 'user':
                user_msg = {"role": "user", "content": msg['content']}
                if 'attachments' in msg:
                    user_msg['attachments'] = msg['attachments']
                messages.append(user_msg)
            elif msg['role'] == 'assistant' and 'stage3' in msg:
                # Only use the final synthesis for history
                messages.append({"role": "assistant", "content": msg['stage3']['response']})
    
    if is_lab_mode:
        # Prompt models to generate PROMPT STRATEGIES
        current_msg = {"role": "user", "content": f"""You are a Prompt Engineer. Your goal is to design a high-performing prompt for the following task:

Task: {user_query}

Provide a comprehensive prompt that would solve this task effectively. 
Focus on:
- Clear instructions
- Proper formatting
- Edge case handling
- Chain-of-thought instructions if appropriate

Directly provide the prompt you would use as your response. Do not add conversational filler."""}
    else:
        current_msg = {"role": "user", "content": user_query}
    
    if attachments:
        current_msg["attachments"] = attachments
    messages.append(current_msg)

    # Query all models in parallel
    responses = await query_models_parallel(COUNCIL_MODELS, messages)

    # Format results
    stage1_results = []
    for model, response in responses.items():
        if response is not None:  # Only include successful responses
            stage1_results.append({
                "model": model,
                "response": response.get('content', '')
            })

    return stage1_results


async def stage2_collect_rankings(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    history: List[Dict[str, Any]] = None,
    test_cases: List[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """
    Stage 2: Each model ranks the anonymized responses or tests prompts.

    Args:
        user_query: The original user query
        stage1_results: Results from Stage 1
        history: Optional conversation history

    Returns:
        Tuple of (rankings list, label_to_model mapping)
    """
    # Create anonymized labels for responses (Response A, Response B, etc.)
    labels = [chr(65 + i) for i in range(len(stage1_results))]  # A, B, C, ...

    # Create mapping from label to model name
    label_to_model = {
        f"Response {label}": result['model']
        for label, result in zip(labels, stage1_results)
    }

    # Build the ranking prompt
    responses_text = "\n\n".join([
        f"Response {label}:\n{result['response']}"
        for label, result in zip(labels, stage1_results)
    ])

    ranking_prompt = f"""You are evaluating different responses to the following question:

Question: {user_query}

Here are the responses from different models (anonymized):

{responses_text}

Your task:
1. First, evaluate each response individually. For each response, explain what it does well and what it does poorly.
2. Then, at the very end of your response, provide a final ranking.

IMPORTANT: Your final ranking MUST be formatted EXACTLY as follows:
- Start with the line "FINAL RANKING:" (all caps, with colon)
- Then list the responses from best to worst as a numbered list
- Each line should be: number, period, space, then ONLY the response label (e.g., "1. Response A")
- Do not add any other text or explanations in the ranking section

Example of the correct format for your ENTIRE response:

Response A provides good detail on X but misses Y...
Response B is accurate but lacks depth on Z...
Response C offers the most comprehensive answer...

FINAL RANKING:
1. Response C
2. Response A
3. Response B

Now provide your evaluation and ranking:"""

    messages = [{"role": "user", "content": ranking_prompt}]

    if test_cases:
        # If test cases exist, we run a "LIVE TEST" loop
        # We query models to EVALUATE the performance of the generated prompts on test cases
        test_case_context = "\n".join([f"Test Input: {tc['input']}\nExpected Output: {tc['expected']}" for tc in test_cases])
        
        evaluation_prompt = f"""You are evaluating different AI prompt strategies for the following task:
Task: {user_query}

TEST CASES:
{test_case_context}

PROMPT VARIATIONS:
{responses_text}

For each prompt variation, explain how well it handles the test cases. 
Identify which one is most reliable and robust.

FINAL RANKING:
(Provide the ranking in the same numbered list format as before)"""
        messages = [{"role": "user", "content": evaluation_prompt}]

    # Get rankings from a subset of fastest models (Stage 2 specialization)
    responses = await query_models_parallel(STAGE2_MODELS, messages)

    # Format results
    stage2_results = []
    for model, response in responses.items():
        if response is not None:
            full_text = response.get('content', '')
            parsed = parse_ranking_from_text(full_text)
            stage2_results.append({
                "model": model,
                "ranking": full_text,
                "parsed_ranking": parsed
            })

    return stage2_results, label_to_model


async def stage3_synthesize_final(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    history: List[Dict[str, Any]] = None,
    is_lab_mode: bool = False
) -> Dict[str, Any]:
    """
    Stage 3: Chairman synthesizes final response or final prompt.

    Args:
        user_query: The original user query
        stage1_results: Individual model responses from Stage 1
        stage2_results: Rankings from Stage 2
        history: Optional conversation history

    Returns:
        Dict with 'model' and 'response' keys
    """
    # Build comprehensive context for chairman
    stage1_text = "\n\n".join([
        f"Model: {result['model']}\nResponse: {result['response']}"
        for result in stage1_results
    ])

    stage2_text = "\n\n".join([
        f"Model: {result['model']}\nRanking: {result['ranking']}"
        for result in stage2_results
    ])

    chairman_prompt = f"""You are the Chairman of an LLM Council. Multiple AI models have provided responses to a user's question, and then ranked each other's responses.

Original Question: {user_query}

STAGE 1 - Individual Responses:
{stage1_text}

STAGE 2 - Peer Rankings:
{stage2_text}

Your task as Chairman is to synthesize all of this information into a single, comprehensive, accurate answer to the user's original question. Consider:
- The individual responses and their insights
- The peer rankings and what they reveal about response quality
- Any patterns of agreement or disagreement

Providing a clear, well-reasoned final answer that represents the council's collective wisdom:"""

    if is_lab_mode:
        chairman_prompt = f"""You are the Chairman of the Prompt Lab. Multiple experts have proposed different prompt engineering strategies for a task, and they have been evaluated against test data.

Original Task: {user_query}

PROPOSED STRATEGIES:
{stage1_text}

PEER EVALUATIONS & TEST RESULTS:
{stage2_text}

Your goal is to synthesize these into the single best possible "Master Prompt". 
Combine the strongest elements of each strategy. Ensure the final prompt is robust, well-formatted, and directly addresses the task requirements.

Output ONLY your final synthesized prompt. No other explanation."""

    messages = []
    if history:
        for msg in history:
            if msg['role'] == 'user':
                messages.append({"role": "user", "content": msg['content']})
            elif msg['role'] == 'assistant' and 'stage3' in msg:
                messages.append({"role": "assistant", "content": msg['stage3']['response']})

    messages.append({"role": "user", "content": chairman_prompt})

    # Query the chairman model
    response = await query_model(CHAIRMAN_MODEL, messages)

    if response is None:
        # Emergency Fallback: If chairman fails, use the best ranked model from Stage 1
        if stage1_results:
            best_model = stage1_results[0]
            # Try to find the actual best model from aggregate rankings if available
            # But here we just use the first available one as final fallback
            return {
                "model": f"Fallback ({best_model['model']})",
                "response": best_model['response']
            }
        
        return {
            "model": CHAIRMAN_MODEL,
            "response": "Error: All models failed. Please check your API keys and quota."
        }

    return {
        "model": CHAIRMAN_MODEL,
        "response": response.get('content', '')
    }


def parse_ranking_from_text(ranking_text: str) -> List[str]:
    """
    Parse the FINAL RANKING section from the model's response.

    Args:
        ranking_text: The full text response from the model

    Returns:
        List of response labels in ranked order
    """
    import re

    # Look for "FINAL RANKING:" section
    if "FINAL RANKING:" in ranking_text:
        # Extract everything after "FINAL RANKING:"
        parts = ranking_text.split("FINAL RANKING:")
        if len(parts) >= 2:
            ranking_section = parts[1]
            # Try to extract numbered list format (e.g., "1. Response A")
            # This pattern looks for: number, period, optional space, "Response X"
            numbered_matches = re.findall(r'\d+\.\s*Response [A-Z]', ranking_section)
            if numbered_matches:
                # Extract just the "Response X" part
                return [re.search(r'Response [A-Z]', m).group() for m in numbered_matches]

            # Fallback: Extract all "Response X" patterns in order
            matches = re.findall(r'Response [A-Z]', ranking_section)
            return matches

    # Fallback: try to find any "Response X" patterns in order
    matches = re.findall(r'Response [A-Z]', ranking_text)
    return matches


def calculate_aggregate_rankings(
    stage2_results: List[Dict[str, Any]],
    label_to_model: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Calculate aggregate rankings across all models.

    Args:
        stage2_results: Rankings from each model
        label_to_model: Mapping from anonymous labels to model names

    Returns:
        List of dicts with model name and average rank, sorted best to worst
    """
    from collections import defaultdict

    # Track positions for each model
    model_positions = defaultdict(list)

    for ranking in stage2_results:
        ranking_text = ranking['ranking']

        # Parse the ranking from the structured format
        parsed_ranking = parse_ranking_from_text(ranking_text)

        for position, label in enumerate(parsed_ranking, start=1):
            if label in label_to_model:
                model_name = label_to_model[label]
                model_positions[model_name].append(position)

    # Calculate average position for each model
    aggregate = []
    for model, positions in model_positions.items():
        if positions:
            avg_rank = sum(positions) / len(positions)
            aggregate.append({
                "model": model,
                "average_rank": round(avg_rank, 2),
                "rankings_count": len(positions)
            })

    # Sort by average rank (lower is better)
    aggregate.sort(key=lambda x: x['average_rank'])

    return aggregate


async def generate_conversation_title(user_query: str) -> str:
    """
    Generate a short title for a conversation based on the first user message.

    Args:
        user_query: The first user message

    Returns:
        A short title (3-5 words)
    """
    title_prompt = f"""Generate a very short title (3-5 words maximum) that summarizes the following question.
The title should be concise and descriptive. Do not use quotes or punctuation in the title.

Question: {user_query}

Title:"""

    messages = [{"role": "user", "content": title_prompt}]

    # Use specialized title model
    response = await query_model(TITLE_MODEL, messages)

    if response is None:
        # Fallback to a generic title
        return "New Conversation"

    title = response.get('content', 'New Conversation').strip()

    # Clean up the title - remove quotes, limit length
    title = title.strip('"\'')

    # Truncate if too long
    if len(title) > 50:
        title = title[:47] + "..."

    return title


async def run_full_council(
    user_query: str, 
    history: List[Dict[str, Any]] = None,
    attachments: List[Dict[str, Any]] = None,
    test_cases: List[Dict[str, Any]] = None
) -> Tuple[List, List, Dict, Dict]:
    """
    Run the complete 3-stage council process.

    Args:
        user_query: The user's question
        history: Optional conversation history
        attachments: Optional list of file attachments
        test_cases: Optional list of test cases for lab mode

    Returns:
        Tuple of (stage1_results, stage2_results, stage3_result, metadata)
    """
    is_lab_mode = test_cases is not None and len(test_cases) > 0

    # Stage 1: Collect individual responses
    stage1_results = await stage1_collect_responses(
        user_query, 
        history=history, 
        attachments=attachments,
        is_lab_mode=is_lab_mode
    )

    # If no models responded successfully, return error
    if not stage1_results:
        return [], [], {
            "model": "error",
            "response": "All models failed to respond. Please try again."
        }, {}

    # Stage 2: Collect rankings
    stage2_results, label_to_model = await stage2_collect_rankings(
        user_query, 
        stage1_results, 
        history=history,
        test_cases=test_cases
    )

    # Calculate aggregate rankings
    aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)

    # Stage 3: Synthesize final answer or prompt
    stage3_result = await stage3_synthesize_final(
        user_query,
        stage1_results,
        stage2_results,
        history=history,
        is_lab_mode=is_lab_mode
    )

    # Prepare metadata
    metadata = {
        "label_to_model": label_to_model,
        "aggregate_rankings": aggregate_rankings
    }

    return stage1_results, stage2_results, stage3_result, metadata
