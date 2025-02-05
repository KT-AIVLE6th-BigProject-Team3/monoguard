document.addEventListener('DOMContentLoaded', function() {
    // ----------- 1) 수정/삭제 (작성자용) -----------
    const editQnaBtn = document.getElementById('editQnaBtn');
    const deleteQnaBtn = document.getElementById('deleteQnaBtn');
    
    const qnaEditModal = document.getElementById('qnaEditModal');
    const closeQnaEditModal = document.getElementById('closeQnaEditModal');
    const qnaEditForm = document.getElementById('qnaEditForm');

    // 현재 게시글 ID (템플릿에서 qna_content.id)
    const qnaId = "{{ qna_content.id }}";

    // (1) 수정 모달 열기
    if (editQnaBtn) {
        editQnaBtn.addEventListener('click', (e) => {
            e.preventDefault();
            qnaEditModal.classList.add('active');
        });
    }

    // 모달 닫기
    if (closeQnaEditModal) {
        closeQnaEditModal.addEventListener('click', () => {
            qnaEditModal.classList.remove('active');
            qnaEditForm.reset();
        });
    }

    // (2) 수정 Form 제출 -> PUT /board/qna/content/{id}/edit
    if (qnaEditForm) {
        qnaEditForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const formData = new FormData(qnaEditForm);

            fetch(`/board/qna/content/${qnaId}/edit`, {
                method: 'PUT',
                body: formData
            })
            .then(res => {
                if (!res.ok) {
                    throw new Error('수정 실패');
                }
                return res.json();
            })
            .then(data => {
                alert("수정이 완료되었습니다.");
                window.location.reload(); // 새로고침 or 목록 이동
            })
            .catch(err => {
                console.error(err);
                alert("수정 중 오류가 발생했습니다.");
            });
        });
    }

    // (3) 삭제 버튼 -> DELETE /board/qna/content/{id}/delete
    if (deleteQnaBtn) {
        deleteQnaBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const confirmed = confirm("정말로 삭제하시겠습니까?");
            if (!confirmed) return;

            fetch(`/board/qna/content/${qnaId}/delete`, {
                method: 'DELETE'
            })
            .then(res => {
                if (!res.ok) throw new Error('삭제 실패');
                return res.text(); // 응답 바디 필요없다면 text()로
            })
            .then(data => {
                alert("삭제되었습니다.");
                window.location.href = "/qna"; // 목록 등 원하는 경로
            })
            .catch(err => {
                console.error(err);
                alert("삭제 중 오류가 발생했습니다.");
            });
        });
    }

    // ----------- 2) 관리자 답변하기/수정 -----------
    const replyBtn = document.getElementById('replyBtn'); // "답변하기" 버튼
    const replyModal = document.getElementById('replyModal');
    const closeReplyModal = document.getElementById('closeReplyModal');
    const replyForm = document.getElementById('replyForm');

    if (replyBtn) {
        replyBtn.addEventListener('click', (e) => {
            e.preventDefault();
            replyModal.classList.add('active');
        });
    }

    if (closeReplyModal) {
        closeReplyModal.addEventListener('click', () => {
            replyModal.classList.remove('active');
            replyForm.reset();
        });
    }

    if (replyForm) {
        replyForm.addEventListener('submit', function(event) {
            event.preventDefault();

            const qnaIdAttr = replyBtn ? replyBtn.getAttribute('data-qna-id') : null;
            if (!qnaIdAttr) {
                alert("게시글 ID를 찾을 수 없습니다.");
                return;
            }

            const formData = new FormData(replyForm);

            // 관리자 답변: PUT /board/qna/content/{id}/reply
            fetch(`/board/qna/content/${qnaIdAttr}/reply`, {
                method: 'PUT',
                body: formData
            })
            .then(res => {
                if (res.ok) {
                    return res.json();
                } else {
                    throw new Error("답변 등록에 실패했습니다.");
                }
            })
            .then(result => {
                alert("답변이 등록되었습니다.");
                window.location.reload();
            })
            .catch(err => {
                console.error(err);
                alert("답변 처리 중 오류가 발생했습니다.");
            });
        });
    }
});