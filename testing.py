import speech_recognition as sr

def record_and_transcribe():
    recognizer = sr.Recognizer()

    # Record audio from the microphone
    with sr.Microphone() as source:
        print("Say something:")
        audio = recognizer.listen(source)
        print("Recording complete.")

    try:
        # Use Google Web Speech API to transcribe the audio
        text = recognizer.recognize_google(audio)
        print("You said:", text)
    except sr.UnknownValueError:
        print("Google Web Speech API could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Web Speech API; {e}")

if __name__ == "__main__":
    record_and_transcribe()
