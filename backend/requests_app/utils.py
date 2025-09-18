from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_request_user(request_obj):
    refresh = RefreshToken.for_user(request_obj)
    refresh['is_request_user'] = True
    refresh['user_id'] = request_obj.id
    refresh['email'] = request_obj.email
    refresh['name'] = request_obj.name
    refresh['surname'] = request_obj.surname
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }
