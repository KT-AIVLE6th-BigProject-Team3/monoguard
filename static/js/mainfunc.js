// 메뉴와 상단바 로드
fetch("/sidebar")
        .then((response) => response.text())
        .then((html) => (document.getElementById("menu").innerHTML = html))
        .catch((error) => console.error("Error loading sidebar:", error));

      fetch("/topbar")
        .then((response) => response.text())
        .then((html) => (document.getElementById("topbar").innerHTML = html))
        .catch((error) => console.error("Error loading topbar:", error));


// `topbar` 로드 및 이벤트 바인딩 함수
document.addEventListener("DOMContentLoaded", function() {
    // 1) topbar 먼저 로드
    fetch("/topbar")
        .then(response => response.text())
        .then(html => {
            document.getElementById("topbar").innerHTML = html;
            // 2) topbar가 로드된 뒤 사용자 정보 불러오기
            updateUserMessageAndAlert();
            attachTopbarEvents();
        })
        .catch(error => console.error("Error loading topbar:", error));
});

// Topbar 이벤트 바인딩 함수
function attachTopbarEvents() {
    console.log("Topbar 이벤트 바인딩 실행됨");
    
    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn && !logoutBtn.dataset.bound) {
        logoutBtn.dataset.bound = "true";  // 중복 실행 방지
        logoutBtn.addEventListener("click", handleLogOut);
    }
}

// 로그아웃 처리 함수
async function handleLogOut() {
    const userConfirmed = confirm("로그아웃 하시겠습니까?");
    if (!userConfirmed) return;

    try {
        const response = await fetch("/auth/logout", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        if (response.ok) {
            alert("로그아웃 하였습니다.");
            window.location.href = "/";
        } else {
            const data = await response.json();
            alert(`로그아웃 실패: ${data.message || "알 수 없는 오류"}`);
        }
    } catch (error) {
        console.error("Error during logout:", error);
        alert("서버와 통신 중 오류가 발생했습니다.");
    }
}

// 사용자 정보 업데이트 함수
function updateUserMessageAndAlert() {
    fetch("/users/message_count")
        .then(response => response.json())
        .then(data => {
            let messageCount = data.message_count;
            let alertCount = data.alert_count;

            let messageBadge = document.getElementById("messageBadge");
            let alertBadge = document.getElementById("alertBadge");

            // 메시지 업데이트
            if (messageBadge) {
                if (messageCount > 0) {
                    messageBadge.textContent = messageCount > 9 ? "9+" : messageCount;
                    messageBadge.style.display = "inline-block";
                } else {
                    messageBadge.style.display = "none";
                }
            }

            // 알림 업데이트
            if (alertBadge) {
                if (alertCount > 0) {
                    alertBadge.textContent = alertCount > 9 ? "9+" : alertCount;
                    alertBadge.style.display = "inline-block";
                } else {
                    alertBadge.style.display = "none";
                }
            }
        })
        .catch(error => console.error("Error updating user message and alerts:", error));
}

// 페이지 이동 시 자동 업데이트
window.addEventListener("popstate", function() {
    updateUserMessageAndAlert();
});

// 페이지가 다시 활성화될 때 실행
document.addEventListener("visibilitychange", function() {
    if (!document.hidden) {
        updateUserMessageAndAlert();
    }
});