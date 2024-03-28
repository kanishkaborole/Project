from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from app.verify import authentication
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from .models import chat_messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .modify import *
import speech_recognition as sr
import re

# Create your views here.
def index(request):
    # return HttpResponse("This is Home page")    
    return render(request, "index.html")

def log_in(request):
    if request.method == "POST":
        # return HttpResponse("This is Home page")  
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username = username, password = password)

        if user is not None:
            login(request, user)
            messages.success(request, "Log In Successful...!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid User...!")
            return redirect("log_in")
    # return HttpResponse("This is Home page")    
    return render(request, "log_in.html")

def register(request):
    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        username = request.POST['username']
        password = request.POST['password']
        password1 = request.POST['password1']
        # print(fname, contact_no, ussername)
        verify = authentication(fname, lname, password, password1)
        if verify == "success":
            user = User.objects.create_user(username, password, password1)          #create_user
            user.first_name = fname
            user.last_name = lname
            user.save()
            messages.success(request, "Your Account has been Created.")
            return redirect("/")
            
        else:
            messages.error(request, verify)
            return redirect("register")
    # return HttpResponse("This is Home page")    
    return render(request, "register.html")

@login_required(login_url="log_in")
@cache_control(no_cache = True, must_revalidate = True, no_store = True)
def log_out(request):
    logout(request)
    messages.success(request, "Log out Successfuly...!")
    return redirect("/")


@login_required(login_url="log_in")
@cache_control(no_cache = True, must_revalidate = True, no_store = True)
def dashboard(request):
    context = {
        'fname': request.user.first_name, 
        }
   
        
    return render(request, "dashboard.html",context)

@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def chat(request, username=None):
    current_user = request.user
    contacts = User.objects.exclude(username__in=['admin', current_user.username])

    last_messages = []
    for contact in contacts:
        last_message = chat_messages.objects.filter(
            Q(sender=current_user, receiver=contact) | Q(sender=contact, receiver=current_user)
        ).order_by('-sendtime').first()

        if last_message:
            message_preview = last_message.message[:30] + "..." # Limit to 30 characters
            sendtime = last_message.sendtime
        else:
            message_preview = ""
            sendtime = None

        last_messages.append({
            'contact': contact,
            'last_message': message_preview,
            'sendtime': sendtime,
        })

    context = {
        'fname': current_user.first_name,
        'contacts': last_messages,
        'current_user': current_user,
    }

    if username is not None:
        # If username is present in the URL, extract the conversation with that user
        other_user = get_object_or_404(User, username=username)
        conversation = chat_messages.objects.filter(
            (Q(sender=current_user, receiver=other_user) | Q(sender=other_user, receiver=current_user))
        ).order_by('sendtime')

        context['conversation'] = conversation
        context['other_user'] = other_user
        context['username'] = username
        context['other_user_first_name'] = other_user.first_name
        context['other_user_last_name'] = other_user.last_name

    return render(request, "chat.html", context)

@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def send_message(request, username):
    if request.method == 'POST':
        current_user = request.user
        other_user = get_object_or_404(User, username=username)
        print(other_user, type(other_user))
        message = request.POST.get('message')
        modified_msg, google_links = modify_msg(message)

        # Modify the message to include formatted links
        response_message = f"""
        Message: {message}
        _______________________________
        Response:
        {modified_msg}
        _______________________________
        Related Links:
        {google_links}
        """
        # Create a new chat message instance
        chat_messages.objects.create(
            sender=current_user,
            receiver=other_user,
            message=response_message,
        )

    return redirect('chat_with_username', username=username)

@login_required(login_url="log_in")
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def record_and_transcribe(request):
    recognizer = sr.Recognizer()

    # Record audio from the microphone
    with sr.Microphone() as source:
        print("Say something...")
        audio = recognizer.listen(source)
        print("Recording complete.")

    try:
        # Use Google Web Speech API to transcribe the audio
        text = recognizer.recognize_google(audio)
        print("You said:", text)

        # Check if the input matches the expected format
        if text.lower().startswith("send") and "to" in text.lower():
            parts = text.split(" ")
            message_index = parts.index("send") + 1
            to_index = parts.index("to")

            # Extract the message and recipient
            message = " ".join(parts[message_index:to_index])
            recipient = " ".join(parts[to_index + 1:])

            # Perform actions with the extracted message and recipient
            print(f"Message: {message}")
            print(f"Recipient: {recipient}")
            # Check if the recipient's name matches any part of the contacts' usernames
            current_user = request.user
            contacts = User.objects.exclude(username__in=['admin', current_user.username])
            print(contacts)
            matching_contact = next((contact for contact in contacts if recipient.lower() in contact.username.lower()), None)
            print(matching_contact)
            if matching_contact:
                # Recipient's name is a part of one of the contacts' usernames
                recipient_username = matching_contact.username
                other_user = get_object_or_404(User, username=recipient_username)

                modified_msg, google_links = modify_msg(message)

                # Modify the message to include formatted links
                response_message = f"""
                Message: {message}
                _______________________________
                Response:
                {modified_msg}
                _______________________________
                Related Links:
                {google_links}
                """
                chat_messages.objects.create(
                    sender=current_user,
                    receiver=other_user,
                    message=response_message,
                )
                # Add your logic to send the message to the recipient
                messages.success(request, f"Message sent to {recipient} ({recipient_username}) successfully.")
            else:
                # Recipient's name is not part of any contacts' usernames
                messages.info(request, f"{recipient} is not in your contacts.")

        else:
            messages.info(request, "Invalid command format. Please use the format 'Send <message> to <recipient>'.")

    except sr.UnknownValueError:
        messages.info(request, "Google Web Speech API could not understand audio")
    except sr.RequestError as e:
        messages.info(request, f"Could not request results from Google Web Speech API; {e}")

    # Get the messages and return as JSON
    response_data = [{'tags': msg.tags, 'message': msg.message} for msg in messages.get_messages(request)]
    return JsonResponse({'messages': response_data})