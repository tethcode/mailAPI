from django.http import JsonResponse
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import FormSubmission
from django.shortcuts import get_object_or_404


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import CustomForm
from .serializers import CustomFormSerializer, FormSubmissionSerializer


@csrf_exempt
def submit_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        if not name or not email or not message:
            return JsonResponse({'error': 'All fields are required!'}, status=400)

        # Save submission in the database
        submission = FormSubmission.objects.create(
            form=CustomForm.objects.first(),  # Assuming the form exists
            data={'name': name, 'email': email, 'message': message}
        )

        # Retrieve latest submission
        submission_data = submission.data
        admin_email = "ekeminithomas37@gmail.com"  # Change to the actual admin email

        # Format email content
        subject = f"New Form Submission: {submission.form.title}"
        email_message = (
            f"New submission received!\n\n"
            f"Name: {submission_data.get('name')}\n"
            f"Email: {submission_data.get('email')}\n"
            f"Message:\n{submission_data.get('message')}\n\n"
            f"Submitted At: {submission.sumitted_at}"
        )

        # Send email to admin
        try:
            send_mail(subject, email_message, settings.EMAIL_HOST_USER, [admin_email])
            return JsonResponse({'message': 'Form submitted and email sent successfully!'})
        except Exception as e:
            return JsonResponse({'error': f'Failed to send email: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)




class CustomFormView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CustomFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FormSubmissionView(APIView):

    permission_classes = [IsAuthenticated]


    def post(self, request, slug):
        form = get_object_or_404(CustomForm, slug=slug)

        # Validate against the dynamic form's fields
        errors = {}
        data = request.data
        for field in form.fields:
            field_name = field['name']
            if field['required'] and field_name not in data:
                errors[field_name] = "This field is required."
        


        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Save the submission
        submission_serializer = FormSubmissionSerializer(data={
            'form': form.id,
            'data': data
        })
        if submission_serializer.is_valid():
            submission_serializer.save()
            return Response({'message': 'Submission successful!'}, status=status.HTTP_201_CREATED)

        return Response(submission_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
