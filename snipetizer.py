import os
import io

# Import libraries
from pydub import AudioSegment
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
from google.cloud.speech_v1 import types
import wave
from google.cloud import storage
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/jackroseman/Desktop/DEV/Bantre/SnippetService/GCP/Bantre-78cdce3b5ad5.json"
filepath = "/Users/jackroseman/Desktop/DEV/Bantre/Data/"     #Input audio file path
# output_filepath = "/Users/jackroseman/Desktop/DEV/Bantre/" #Final transcript path
bucketname = "bantre_podcast_data" #Name of the bucket created in the step before

def mp3_to_wav(audio_file_name):
    if audio_file_name.split('.')[1] == 'mp3':    
        sound = AudioSegment.from_mp3(audio_file_name)
        audio_file_name = audio_file_name.split('.')[0] + '.wav'
        sound.export(audio_file_name, format="wav")

def stereo_to_mono(audio_file_name):
    sound = AudioSegment.from_wav(audio_file_name)
    sound = sound.set_channels(1)
    sound.export(audio_file_name, format="wav")

def frame_rate_channel(audio_file_name):
    with wave.open(audio_file_name, "rb") as wave_file:
        frame_rate = wave_file.getframerate()
        channels = wave_file.getnchannels()
        return frame_rate,channels

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.delete()

def transcribe(audio_file_name):
    
    file_name = filepath + audio_file_name
    # mp3_to_wav(file_name)

    # # The name of the audio file to transcribe
    
    frame_rate, channels = frame_rate_channel(file_name)
    
    if channels > 1:
        stereo_to_mono(file_name)
    
    upload_blob(bucketname, file_name, audio_file_name)
    
    gcs_uri = 'gs://' + bucketname + '/' + audio_file_name
    transcript = ''
    
    client = speech_v1.SpeechClient()
    audio = {"uri": gcs_uri}
    config = {
        "sample_rate_hertz": frame_rate,
        "language_code": 'en-US',
        "encoding": enums.RecognitionConfig.AudioEncoding.LINEAR16,
    }
    operation = client.long_running_recognize(config, audio)
    response = operation.result(timeout=10000)

    for result in response.results:
        transcript += result.alternatives[0].transcript
    
    delete_blob(bucketname, audio_file_name)
    return transcript

with io.open("Another_Way-S3E45-Colorado_Electors.txt", "w") as f:
    f.write(transcribe("Another_Way-S3E45-Colorado_Electors.wav"))
f.close()