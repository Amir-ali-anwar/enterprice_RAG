"""RAGAS metrics using Groq for judging and Hugging Face API embeddings."""

import asyncio
import os

from dotenv import load_dotenv
import logfire
from openai import AsyncOpenAI
import pandas as pd
from ragas.llms import llm_factory
from ragas.metrics.collections import (
	AnswerCorrectness,
	AnswerRelevancy,
	ContextPrecision,
	ContextRecall,
	Faithfulness,
)


GROQ_BASE_URL = "https://api.groq.com/openai/v1"
JUDGE_MODEL = "llama-3.1-8b-instant"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

COOLDOWN_STANDARD = 62
COOLDOWN_MINI = 40
GENERAL_BATCH_SIZE = 1
CONTEXT_LIMIT = 2
CONTEXT_TRUNCATE = 600
MAX_RETRIES = 8
RETRY_BASE_DELAY = 60.0
MAX_RETRY_WAIT = 300.0

load_dotenv()


def _build_judge():
	"""Create the Groq judge and hosted Hugging Face embedding client."""
	api_key = os.getenv("JUDGE_GROQ") or os.getenv("GROQ_API_KEY")
	if not api_key:
		raise ValueError("Set JUDGE_GROQ or GROQ_API_KEY to run RAGAS metrics.")

	hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
	if not hf_token:
		raise ValueError(
			"Set HF_TOKEN or HUGGINGFACEHUB_API_TOKEN to run Hugging Face embeddings."
		)

	from ragas.embeddings import HuggingFaceEmbeddings

	client = AsyncOpenAI(api_key=api_key, base_url=GROQ_BASE_URL)
	judge_llm = llm_factory(JUDGE_MODEL, provider="openai", client=client)
	embeddings = HuggingFaceEmbeddings(
		model=EMBEDDING_MODEL,
		use_api=True,
		api_key=hf_token,
		normalize_embeddings=True,
	)
	return judge_llm, embeddings


async def _cooldown(seconds: int, label: str, status_cb=None):
	if status_cb:
		status_cb(f"Cooldown after {label}: {seconds}s")
	await asyncio.sleep(seconds)
	if status_cb:
		status_cb("Ready for the next experiment.")


def _prep_samples(golden_dataset: dict) -> list[dict]:
	"""Trim live responses and available contexts for the RAGAS input budget."""
	samples = []
	for sample in golden_dataset["rag_samples"]:
		response = sample.get("actual_response", "").strip()
		if not response:
			continue

		raw_contexts = sample.get("actual_contexts") or sample.get(
			"relevant_contexts", []
		)
		contexts = [
			str(context)[:CONTEXT_TRUNCATE]
			for context in raw_contexts[:CONTEXT_LIMIT]
		]
		samples.append({**sample, "actual_contexts": contexts})
	return samples


def _score_df(metric_key: str, samples: list[dict], scores) -> pd.DataFrame:
	return pd.DataFrame(
		[
			{"question": sample["question"][:65], metric_key: round(float(score.value), 3)}
			for sample, score in zip(samples, scores)
		]
	)


async def _batched_score(metric, inputs: list[dict], status_cb=None, label: str = ""):
	"""Score one sample at a time and back off only for API rate limits."""
	scores = []
	for index, item in enumerate(inputs):
		if index:
			await _cooldown(COOLDOWN_MINI, f"{label} sample {index}", status_cb)

		for attempt in range(MAX_RETRIES):
			try:
				scores.extend(await metric.abatch_score([item]))
				break
			except Exception as error:
				is_rate_limit = any(
					marker in str(error).lower() for marker in ("429", "rate", "limit")
				)
				if not is_rate_limit or attempt == MAX_RETRIES - 1:
					raise

				wait = min(RETRY_BASE_DELAY * (2**attempt), MAX_RETRY_WAIT)
				logfire.warning(
					"Metric rate limited",
					metric=label,
					sample=index + 1,
					retry=attempt + 1,
					wait_seconds=wait,
				)
				if status_cb:
					status_cb(
						f"Rate limited on {label} sample {index + 1}; waiting {wait:.0f}s."
					)
				await asyncio.sleep(wait)
	return scores


async def _run_metric(metric_key: str, metric, inputs: list[dict], samples: list[dict], status_cb=None):
	scores = await _batched_score(metric, inputs, status_cb, metric_key)
	result = _score_df(metric_key, samples, scores)
	logfire.info("Metric complete", metric=metric_key, average=result[metric_key].mean())
	return result


async def run_all_metrics(golden_dataset: dict, status_cb=None) -> dict[str, pd.DataFrame]:
	"""Run five RAGAS experiments plus tool correctness over live responses."""
	judge_llm, embeddings = _build_judge()
	samples = _prep_samples(golden_dataset)
	if not samples:
		raise ValueError("No samples with actual_response found. Run the live pipeline first.")

	results = {}
	experiments = [
		(
			"faithfulness",
			Faithfulness(llm=judge_llm),
			lambda sample: {
				"user_input": sample["question"],
				"response": sample["actual_response"],
				"retrieved_contexts": sample["actual_contexts"],
			},
		),
		(
			"answer_relevancy",
			AnswerRelevancy(llm=judge_llm, embeddings=embeddings),
			lambda sample: {
				"user_input": sample["question"],
				"response": sample["actual_response"],
			},
		),
		(
			"context_precision",
			ContextPrecision(llm=judge_llm),
			lambda sample: {
				"user_input": sample["question"],
				"reference": sample["reference"],
				"retrieved_contexts": sample["actual_contexts"],
			},
		),
		(
			"context_recall",
			ContextRecall(llm=judge_llm),
			lambda sample: {
				"user_input": sample["question"],
				"reference": sample["reference"],
				"retrieved_contexts": sample["actual_contexts"],
			},
		),
		(
			"answer_correctness",
			AnswerCorrectness(llm=judge_llm, embeddings=embeddings),
			lambda sample: {
				"user_input": sample["question"],
				"response": sample["actual_response"],
				"reference": sample["reference"],
			},
		),
	]

	for index, (key, metric, input_builder) in enumerate(experiments, start=1):
		if status_cb:
			status_cb(f"Experiment {index}/6: {key} ({len(samples)} samples)")
		inputs = [input_builder(sample) for sample in samples]
		results[key] = await _run_metric(key, metric, inputs, samples, status_cb)
		if index < len(experiments):
			await _cooldown(COOLDOWN_STANDARD, key, status_cb)

	tool_rows = []
	for sample in samples:
		actual = set(sample.get("actual_tools_called") or [])
		expected = set(sample.get("expected_tools") or [])
		union = actual | expected
		tool_rows.append(
			{
				"question": sample["question"][:65],
				"tool_correctness": round(len(actual & expected) / len(union), 3)
				if union
				else 0.0,
			}
		)
	results["tool_correctness"] = pd.DataFrame(tool_rows)
	if status_cb:
		status_cb("All six experiments complete.")
	return results
