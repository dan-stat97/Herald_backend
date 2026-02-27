# Follows API Documentation

## Endpoints

### Follow a User
- **POST** `/api/v1/users/<user_id>/follow/`
- Auth required: Yes
- Response: `{ "success": true }` or `{ "error": "Already following" }`

### Unfollow a User
- **DELETE** `/api/v1/users/<user_id>/unfollow/`
- Auth required: Yes
- Response: `{ "success": true }`

### List Followers
- **GET** `/api/v1/users/<user_id>/followers/`
- Auth required: Yes
- Response: `[{ "id": <uuid>, "username": <str>, "display_name": <str> }, ...]`

### List Following
- **GET** `/api/v1/users/<user_id>/following/`
- Auth required: Yes
- Response: `[{ "id": <uuid>, "username": <str>, "display_name": <str> }, ...]`

## Example Usage

- To follow a user: `POST /api/v1/users/123e4567-e89b-12d3-a456-426614174000/follow/`
- To unfollow: `DELETE /api/v1/users/123e4567-e89b-12d3-a456-426614174000/unfollow/`
- To get followers: `GET /api/v1/users/123e4567-e89b-12d3-a456-426614174000/followers/`
- To get following: `GET /api/v1/users/123e4567-e89b-12d3-a456-426614174000/following/`

## Notes
- All endpoints require JWT authentication.
- Returns 409 if already following.
- Returns 200 and success for idempotent unfollow.
