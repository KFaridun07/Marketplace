from groq import Groq
from django.conf import settings


client = Groq(api_key=settings.GROQ_API_KEY)


def ask_ai(question, products):

    products_text = ""

    for product in products:
        products_text += f"""
Product ID: {product.id}
Product: {product.name}
Category: {product.category}
Price: {product.price}
Description: {product.description}

"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": f"""
You are an AI assistant for an online marketplace.

Your main job is to help users find and understand products
available in our marketplace.

Use ONLY the product information provided below when answering
questions about marketplace products.

You can:
- find products
- compare products
- compare prices
- recommend products based on the user's requirements
- explain product descriptions
- tell the user which category a product belongs to

If a requested product is not in the marketplace data,
say that this product is not available.

Do not invent products, prices, categories or descriptions.

Marketplace products:

{products_text}
"""
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    return response.choices[0].message.content