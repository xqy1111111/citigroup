import React from 'react';

interface ModalProps {
    children: React.ReactNode;
    onClose?: () => void;
}

function Modal({ children, onClose }: ModalProps) {
    return (
        <div className="modal-overlay">
            <div className="modal">
                {children}
            </div>
        </div>
    );
}

export default Modal; 