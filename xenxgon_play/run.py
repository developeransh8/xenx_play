from waitress import serve
from app import app
import config
import logging

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info(f"Starting xenXgon Play on {config.HOST}:{config.PORT}")
    print(f"\n{'='*60}")
    print(f"  xenXgon Play Video Streaming Server")
    print(f"  Listening on http://{config.HOST}:{config.PORT}")
    print(f"{'='*60}\n")
    
    serve(
        app,
        host=config.HOST,
        port=config.PORT,
        channel_timeout=600,
        threads=6,
        url_scheme='http',
        max_request_body_size=int(config.MAX_UPLOAD_SIZE),
        inbuf_overflow=int(config.MAX_UPLOAD_SIZE),
        outbuf_overflow=int(config.MAX_UPLOAD_SIZE)
    )
