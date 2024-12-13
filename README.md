# Image-Classification-and-Grading
Many business problems related to image classification and grading remain unsolved due to the extensive effort required for obtaining ground truth data, processing large datasets, and building complex Deep Neural Network (DNN) models. Moreover, even with significant investment in these processes, there is no guarantee of achieving strong model performance.

My aim is to demonstrate how multi-modal LLMs such as Google Gemini can significantly reduce the time and improve the confidence in solving such business problems, compared with building Deep Neural Nets such as CNN using Tensorflow framework.

This repository includes:
1. A PDF detailing architectures for two different AI solutions on the AWS platform:
   1. A CNN model for image classification
   2. A serverless approach using Google Gemini 1.5_pro_002 API for image classification and grading 
2. Requirements for both AI solutions
3. Jupyter Notebooks for the development and execution of both approaches
4. AWS Lambda Functions for implementing the serverless approach with LLMs

**Performance:**

**Dataset:**
   Huggingface dataset has been used to train, test, validate the CNN model, and to validate Google Gemini LLM API wrapper.
   
**Results:**
1. CNN Model:
   Classification Accuracy of CNN Model trained on 2000 images: 13.6%
2. Google Gemini LLM API Wrapper:
   Classification Accuracy: 95%
   Grading Accuracy: 60%
   _Note:_The performance is highly dependent on Prompt Engineering, and fine-tuning the prompt can further imprve the performance

**AWS Technology Stack**
1. AWS Lambda
Serverless architecture for scalable processing of food images.
Invoked a Lambda function by invoker Lambda function. Special IAM roles have to be created to provide invoke access to Lambda functions
Implemented data preprocessing and Google Gemini API wrapper triggers for inference tasks
3. AWS SageMaker
Hosted and deployed the trained CNN model.
Conducted large-scale model training and optimization.
4. AWS S3
Stored datasets and model artifacts.
