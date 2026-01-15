from bytez import Bytez

# insert your key
sdk = Bytez("1ef94f908fe1457aa92d55e55b2926c9")

# choose your model
model = sdk.model("google/gemma-3-4b-it")

# provide the model with input
input = [
  {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "Describe this image"
      },
      {
        "type": "image",
        "url": "https://hips.hearstapps.com/hmg-prod/images/how-to-keep-ducks-call-ducks-1615457181.jpg?crop=0.670xw:1.00xh;0.157xw,0&resize=980:*"
      }
    ]
  }
]

# send to the model
result = model.run(input)

# observe the output
print({"error": result.error, "output": result.output})