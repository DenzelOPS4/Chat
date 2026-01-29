from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import openai
import os

class ChatView(APIView):
    def post(self, request):
        user_text = request.data.get('text', '')
        if not user_text:
            return Response({'error': 'No text provided'}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('BASE_URL')

        if not api_key:
             return Response({'error': 'Server configuration error: OpenAI API key missing'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        client = openai.OpenAI(api_key=api_key, base_url=base_url)

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": user_text,
                    }
                ],
                model="deepseek/deepseek-r1-0528:free",
            )
            bot_response = chat_completion.choices[0].message.content
            return Response({'response': bot_response})

        except openai.APIConnectionError as e:
            print(f"OpenAI Connection Error: {e}")
            return Response({'error': 'Failed to connect to OpenAI API. Please check your network connection.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except openai.RateLimitError as e:
            print(f"OpenAI Rate Limit Error: {e}")
            return Response({'error': 'OpenAI API rate limit exceeded. Please try again later.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except openai.APIError as e:
            print(f"OpenAI API Error: {e}")
            return Response({'error': f"OpenAI API returned an error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            print(f"Unexpected Error: {e}")
            return Response({'error': 'An unexpected error occurred on the server.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
