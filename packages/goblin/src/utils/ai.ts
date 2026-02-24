import { createOpenRouter } from '@openrouter/ai-sdk-provider';
import { generateText } from 'ai';

export const DEFAULT_MODEL = 'google/gemini-3-flash';

let openrouterProvider: ReturnType<typeof createOpenRouter> | null = null;

function getProvider(): ReturnType<typeof createOpenRouter> {
  if (openrouterProvider) {
    return openrouterProvider;
  }
  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    throw new Error('OPENROUTER_API_KEY is required to run transform.');
  }
  openrouterProvider = createOpenRouter({ apiKey });
  return openrouterProvider;
}

export async function runPrompt(prompt: string, model: string): Promise<string> {
  const openrouter = getProvider();
  const { text } = await generateText({
    model: openrouter(model),
    prompt,
  });
  return text;
}
