ZnJvbSBzcWxhbGNoZW15IGltcG9ydCBDb2x1bW4sIEludGVnZXIsIFN0cmlu
ZywgRGF0ZVRpbWUKZnJvbSBzcWxhbGNoZW15LnNxbCBpbXBvcnQgZnVuYwpm
cm9tIGFwcC5jb3JlLmRhdGFiYXNlIGltcG9ydCBCYXNlCgpjbGFzcyBQcm94
eShCYXNlKToKICAgIF9fdGFibGVuYW1lX18gPSAicHJveGllcyIKCiAgICBp
ZCA9IENvbHVtbihJbnRlZ2VyLCBwcmltYXJ5X2tleT1UcnVlLCBpbmRleD1U
cnVlKQogICAgdXJsID0gQ29sdW1uKFN0cmluZywgdW5pcXVlPVRydWUsIG51
bGxhYmxlPUZhbHNlKSAgIyBob3N0OnBvcnQKICAgIHVzZXJuYW1lID0gQ29s
dW1uKFN0cmluZywgbnVsbGFibGU9VHJ1ZSkKICAgIHBhc3N3b3JkID0gQ29s
dW1uKFN0cmluZywgbnVsbGFibGU9VHJ1ZSkKICAgIHByb3RvY29sID0gQ29s
dW1uKFN0cmluZywgZGVmYXVsdD0iaHR0cCIpICAjIGh0dHAsIHNvY2tzNQog
ICAgY291bnRyeSA9IENvbHVtbihTdHJpbmcsIG51bGxhYmxlPVRydWUpCiAg
ICBzdGF0dXMgPSBDb2x1bW4oU3RyaW5nLCBkZWZhdWx0PSJhY3RpdmUiKSAg
IyBhY3RpdmUsIGRpc2FibGVkLCBiYW5uZWQKICAgIGxhc3RfdXNlZCA9IENv
bHVtbihEYXRlVGltZSh0aW1lem9uZT1UcnVlKSwgbnVsbGFibGU9VHJ1ZSkK
ICAgIGZhaWxfY291bnQgPSBDb2x1bW4oSW50ZWdlciwgZGVmYXVsdD0wKQog
ICAgc3VjY2Vzc19jb3VudCA9IENvbHVtbihJbnRlZ2VyLCBkZWZhdWx0PTAp
CiAgICBjcmVhdGVkX2F0ID0gQ29sdW1uKERhdGVUaW1lKHRpbWV6b25lPVRy
dWUpLCBzZXJ2ZXJfZGVmYXVsdD1mdW5jLm5vdygpKQ==
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Proxy(Base):
    __tablename__ = "proxies"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    password = Column(String, nullable=True)
    protocol = Column(String, default="http")
    country = Column(String, nullable=True)
    status = Column(String, default="active")
    last_used = Column(DateTime(timezone=True), nullable=True)
    fail_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
