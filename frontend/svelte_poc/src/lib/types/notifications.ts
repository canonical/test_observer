export type NotificationType =
  | 'USER_ASSIGNED_ARTEFACT_REVIEW'
  | 'USER_ASSIGNED_ENVIRONMENT_REVIEW';

export interface UserNotification {
  id: number;
  user_id: number;
  notification_type: NotificationType;
  target_url: string | null;
  created_at: string;
  dismissed_at: string | null;
}

export interface UserNotifications {
  notifications: UserNotification[];
}

export interface UnreadCountResponse {
  count: number;
}

export function notificationDisplayTitle(type: NotificationType): string {
  switch (type) {
    case 'USER_ASSIGNED_ARTEFACT_REVIEW':
      return 'Artefact Review Assigned';
    case 'USER_ASSIGNED_ENVIRONMENT_REVIEW':
      return 'Environment Review Assigned';
  }
}
