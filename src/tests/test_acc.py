from http import HTTPStatus

import pytest
from flask import json, url_for

EMAIL = 'test1@test.test'
PASSWORD = 'test1Test-'
USER_CRED = json.dumps({'email': EMAIL, 'password': PASSWORD})


def test_signup(client, db):
    url = url_for('api_v1.signup')
    response = client.post(url, data=USER_CRED, content_type='application/json')
    assert response.status_code == HTTPStatus.CREATED
    assert 'access_token' in response.json
    assert 'access_token_expired_utc' in response.json
    assert 'refresh_token' in response.json
    assert 'refresh_token_expired_utc' in response.json


def test_signup_errors(client, user):
    url = url_for('api_v1.signup')
    # Передаем занятый email
    assert client.post(url, data=USER_CRED, content_type='application/json').status_code == HTTPStatus.CONFLICT
    # Передаем не email
    data = {'email': 'jfhsjkfhskjdh', 'password': PASSWORD}
    assert client.post(url, data=json.dumps(
        data), content_type='application/json').status_code == HTTPStatus.BAD_REQUEST
    # Передаем короткий пароль
    data = {'email': EMAIL, 'password': 'bvbvhf'}
    assert client.post(url, data=json.dumps(
        data), content_type='application/json').status_code == HTTPStatus.BAD_REQUEST


def test_login(client, user):
    response = client.post(url_for('api_v1.login'), data=USER_CRED, content_type='application/json')
    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json
    assert 'access_token_expired_utc' in response.json
    assert 'refresh_token' in response.json
    assert 'refresh_token_expired_utc' in response.json


def test_login_errors(client):
    # Посылаем рандомные данные
    data = {'email': EMAIL + 'a', 'password': PASSWORD + 'a'}
    assert client.post(url_for('api_v1.login'), data=json.dumps(
        data), content_type='application/json').status_code == HTTPStatus.UNAUTHORIZED


@pytest.mark.parametrize('endpoint', ('api_v1.signup', 'api_v1.login'))
@pytest.mark.parametrize('email, password', (('name', 'password'), ('email', 'pasword'), ('name', 'pasword')))
def test_signup_login_wrong_param(client, db, user, endpoint, email, password):
    # Передаем неверные ключи
    data = {email: EMAIL, password: PASSWORD}
    response = client.post(url_for(endpoint), data=json.dumps(data), content_type='application/json')
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_logout(client, auth_user):
    headers = {'Authorization': f'Bearer {auth_user["access_token"]}'}
    response = client.delete(url_for('api_v1.logout'), headers=headers)
    assert response.status_code == HTTPStatus.OK
    # Токены отозваны, проверяем что не можем авторизоваться и рефрешнуть токены
    response = client.get(url_for('api_v1.auth'), headers=headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json['msg'] == 'Token has been revoked'
    response = client.post(url_for('api_v1.refresh'), headers={'Authorization': f'Bearer {auth_user["refresh_token"]}'})
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json['msg'] == 'Token has been revoked'


def test_logout_errors(client, auth_user):
    # Отправляем refresh вместо access
    url = url_for('api_v1.logout')
    headers = {'Authorization': f'Bearer {auth_user["refresh_token"]}'}
    assert client.delete(url, headers=headers).status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    # Отправляем запрос без токена
    headers = {'Authorization': 'Bearer '}
    assert client.delete(url, headers=headers).status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_comp_logout(client, user, auth_user):
    # Создаем еще пару токенов для юзера
    clone1 = client.post(url_for('api_v1.login'), data=USER_CRED, content_type='application/json').json
    clone2 = client.post(url_for('api_v1.login'), data=USER_CRED, content_type='application/json').json
    assert clone1 != clone2
    # Проверяем что все токены валидны
    for user in (auth_user, clone1, clone2):
        assert client.get(url_for('api_v1.auth'), headers={
                          'Authorization': f'Bearer {user["access_token"]}'}) == HTTPStatus.OK
    # Отзываем все токены юзера
    response = client.delete(url_for('api_v1.completely_logout'), headers={
        'Authorization': f'Bearer {auth_user["access_token"]}'})
    assert response.status_code == HTTPStatus.OK
    # Запоминаем новые токены
    auth_user = response.json
    # Проверяем что все токены отозваны
    for user in (clone1, clone2):
        assert client.get(url_for('api_v1.auth'), headers={
                          'Authorization': f'Bearer {user["access_token"]}'}) == HTTPStatus.UNAUTHORIZED
        assert client.post(url_for('api_v1.refresh'), headers={
            'Authorization': f'Bearer {user["refresh_token"]}'}) == HTTPStatus.UNAUTHORIZED
    # Проверяем что вновь выданные токены валидны
    assert client.get(url_for('api_v1.auth'), headers={
        'Authorization': f'Bearer {auth_user["access_token"]}'}) == HTTPStatus.OK
    assert client.post(url_for('api_v1.refresh'), headers={
        'Authorization': f'Bearer {auth_user["refresh_token"]}'}) == HTTPStatus.OK


def test_refresh(client, auth_user):
    headers = {'Authorization': f'Bearer {auth_user["refresh_token"]}'}
    response = client.post(url_for('api_v1.refresh'), headers=headers)
    assert response.status_code == HTTPStatus.OK
    assert 'access_token' in response.json
    assert 'access_token_expired_utc' in response.json
    assert 'refresh_token' in response.json
    assert 'refresh_token_expired_utc' in response.json
    # Проверяем что второй раз токен не сработает
    assert client.post(url_for('api_v1.refresh'), headers=headers).status_code == HTTPStatus.UNAUTHORIZED


def test_refresh_errors(client, auth_user):
    # Отправляем access вместо refresh
    url = url_for('api_v1.refresh')
    headers = {'Authorization': f'Bearer {auth_user["access_token"]}'}
    assert client.post(url, headers=headers).status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    # Отправляем запрос без токена
    headers = {'Authorization': 'Bearer '}
    assert client.post(url, headers=headers).status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_changing(client, auth_user):
    new_email = EMAIL + 'a'
    new_password = PASSWORD + 'a'
    headers = {'Authorization': f'Bearer {auth_user["access_token"]}'}
    data = {'email': new_email, 'password': new_password}
    response = client.patch(url_for('api_v1.changing'), data=json.dumps(data),
                            headers=headers, content_type='application/json')
    assert response.status_code == HTTPStatus.OK
    # Проверяем что токен отозван
    response = client.get(url_for('api_v1.auth'), headers=headers)
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    # Проверяем что можем залогиниться с новыми данными,
    response = client.post(url_for('api_v1.login'), data=json.dumps(data), content_type='application/json')
    assert response.status_code == HTTPStatus.OK
    # а со старыми не можем
    response = client.post(url_for('api_v1.login'), data=USER_CRED, content_type='application/json')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_changing_errors(client, auth_user):
    url = url_for('api_v1.changing')
    headers = {'Authorization': f'Bearer {auth_user["access_token"]}'}
    # Отправляем запрос без токена
    assert client.patch(url, data=USER_CRED, headers={'Authorization': 'Bearer '}).status_code == HTTPStatus.BAD_REQUEST
    # Передаем не email
    data = {'email': 'jfhsjkfhskjdh', 'password': PASSWORD}
    assert client.patch(url, data=json.dumps(
        data), headers=headers, content_type='application/json').status_code == HTTPStatus.BAD_REQUEST
    # Передаем короткий пароль
    data = {'email': EMAIL, 'password': 'bvbvhf'}
    assert client.patch(url, data=json.dumps(
        data), headers=headers, content_type='application/json').status_code == HTTPStatus.BAD_REQUEST


def test_history(client, auth_user):
    headers = {'Authorization': f'Bearer {auth_user["access_token"]}'}
    response = client.get(url_for('api_v1.history'), headers=headers)
    assert response.status_code == HTTPStatus.OK
    assert 'LogIn success' in response.json[0]['action']


def test_history_errors(client):
    # Отправляем запрос без токена
    assert client.get(url_for('api_v1.history'), headers={
                      'Authorization': 'Bearer '}).status_code == HTTPStatus.UNPROCESSABLE_ENTITY
