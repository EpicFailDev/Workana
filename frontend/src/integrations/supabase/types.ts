export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  __InternalSupabase: {
    PostgrestVersion: "14.1"
  }
  public: {
    Tables: {
      activity_logs: {
        Row: {
          id: number
          user_id: string
          action_type: string
          action_description: string
          details: Json | null
          project_id: number | null
          status: string | null
          error_message: string | null
          ip_address: string | null
          user_agent: string | null
          duration_ms: number | null
          created_at: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          action_type: string
          action_description: string
          details?: Json | null
          project_id?: number | null
          status?: string | null
          error_message?: string | null
          ip_address?: string | null
          user_agent?: string | null
          duration_ms?: number | null
          created_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          action_type?: string
          action_description?: string
          details?: Json | null
          project_id?: number | null
          status?: string | null
          error_message?: string | null
          ip_address?: string | null
          user_agent?: string | null
          duration_ms?: number | null
          created_at?: string | null
        }
        Relationships: []
      }
      automation_config: {
        Row: {
          id: number
          user_id: string
          headless: boolean | null
          delay_between_actions_ms: number | null
          max_proposals_per_day: number | null
          auto_apply: boolean | null
          preferred_template_id: number | null
          updated_at: string | null
          gemini_api_key: string | null
          user_full_name: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          headless?: boolean | null
          delay_between_actions_ms?: number | null
          max_proposals_per_day?: number | null
          auto_apply?: boolean | null
          preferred_template_id?: number | null
          updated_at?: string | null
          gemini_api_key?: string | null
          user_full_name?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          headless?: boolean | null
          delay_between_actions_ms?: number | null
          max_proposals_per_day?: number | null
          auto_apply?: boolean | null
          preferred_template_id?: number | null
          updated_at?: string | null
          gemini_api_key?: string | null
          user_full_name?: string | null
        }
        Relationships: []
      }
      blacklisted_clients: {
        Row: {
          id: number
          user_id: string
          client_name: string
          reason: string | null
          created_at: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          client_name: string
          reason?: string | null
          created_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          client_name?: string
          reason?: string | null
          created_at?: string | null
        }
        Relationships: []
      }
      credentials: {
        Row: {
          id: number
          user_id: string
          email: string
          encrypted_password: string
          created_at: string | null
          updated_at: string | null
        }
        Insert: {
          id?: number
          user_id: string
          email: string
          encrypted_password: string
          created_at?: string | null
          updated_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          email?: string
          encrypted_password?: string
          created_at?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      daily_statistics: {
        Row: {
          id: number
          user_id: string
          date: string
          projects_found: number | null
          projects_viewed: number | null
          proposals_sent: number | null
          proposals_accepted: number | null
          proposals_rejected: number | null
          logins_count: number | null
          searches_count: number | null
          errors_count: number | null
          total_time_spent_minutes: number | null
          created_at: string | null
          updated_at: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          date: string
          projects_found?: number | null
          projects_viewed?: number | null
          proposals_sent?: number | null
          proposals_accepted?: number | null
          proposals_rejected?: number | null
          logins_count?: number | null
          searches_count?: number | null
          errors_count?: number | null
          total_time_spent_minutes?: number | null
          created_at?: string | null
          updated_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          date?: string
          projects_found?: number | null
          projects_viewed?: number | null
          proposals_sent?: number | null
          proposals_accepted?: number | null
          proposals_rejected?: number | null
          logins_count?: number | null
          searches_count?: number | null
          errors_count?: number | null
          total_time_spent_minutes?: number | null
          created_at?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      profile_config: {
        Row: {
          id: number
          user_id: string
          profile_url: string
          auto_sync_enabled: boolean | null
          sync_interval_hours: number | null
          last_sync_at: string | null
          created_at: string | null
          updated_at: string | null
        }
        Insert: {
          id?: number
          user_id: string
          profile_url: string
          auto_sync_enabled?: boolean | null
          sync_interval_hours?: number | null
          last_sync_at?: string | null
          created_at?: string | null
          updated_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          profile_url?: string
          auto_sync_enabled?: boolean | null
          sync_interval_hours?: number | null
          last_sync_at?: string | null
          created_at?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      profile_metrics: {
        Row: {
          id: number
          user_id: string
          profile_url: string
          username: string | null
          display_name: string | null
          projects_completed: number | null
          projects_in_progress: number | null
          hours_worked: number | null
          average_rating: number | null
          total_reviews: number | null
          member_since: string | null
          country: string | null
          hourly_rate: string | null
          skills: Json | null
          last_login: string | null
          profile_photo_url: string | null
          scraped_at: string | null
        }
        Insert: {
          id?: number
          user_id: string
          profile_url: string
          username?: string | null
          display_name?: string | null
          projects_completed?: number | null
          projects_in_progress?: number | null
          hours_worked?: number | null
          average_rating?: number | null
          total_reviews?: number | null
          member_since?: string | null
          country?: string | null
          hourly_rate?: string | null
          skills?: Json | null
          last_login?: string | null
          profile_photo_url?: string | null
          scraped_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          profile_url?: string
          username?: string | null
          display_name?: string | null
          projects_completed?: number | null
          projects_in_progress?: number | null
          hours_worked?: number | null
          average_rating?: number | null
          total_reviews?: number | null
          member_since?: string | null
          country?: string | null
          hourly_rate?: string | null
          skills?: Json | null
          last_login?: string | null
          profile_photo_url?: string | null
          scraped_at?: string | null
        }
        Relationships: []
      }
      projects: {
        Row: {
          id: number
          user_id: string
          workana_id: string
          title: string
          description: string | null
          url: string
          category: string | null
          subcategory: string | null
          budget_min: number | null
          budget_max: number | null
          budget_type: string | null
          deadline: string | null
          skills: Json | null
          client_name: string | null
          client_country: string | null
          client_rating: number | null
          client_projects_posted: number | null
          proposals_count: number | null
          is_favorite: boolean | null
          is_applied: boolean | null
          is_ignored: boolean | null
          notes: string | null
          found_at: string | null
          updated_at: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          workana_id: string
          title: string
          description?: string | null
          url: string
          category?: string | null
          subcategory?: string | null
          budget_min?: number | null
          budget_max?: number | null
          budget_type?: string | null
          deadline?: string | null
          skills?: Json | null
          client_name?: string | null
          client_country?: string | null
          client_rating?: number | null
          client_projects_posted?: number | null
          proposals_count?: number | null
          is_favorite?: boolean | null
          is_applied?: boolean | null
          is_ignored?: boolean | null
          notes?: string | null
          found_at?: string | null
          updated_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          workana_id?: string
          title?: string
          description?: string | null
          url?: string
          category?: string | null
          subcategory?: string | null
          budget_min?: number | null
          budget_max?: number | null
          budget_type?: string | null
          deadline?: string | null
          skills?: Json | null
          client_name?: string | null
          client_country?: string | null
          client_rating?: number | null
          client_projects_posted?: number | null
          proposals_count?: number | null
          is_favorite?: boolean | null
          is_applied?: boolean | null
          is_ignored?: boolean | null
          notes?: string | null
          found_at?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      proposal_history: {
        Row: {
          id: number
          user_id: string
          project_id: string
          project_title: string
          project_url: string | null
          budget: number
          deadline_days: number
          message: string | null
          status: string | null
          sent_at: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          project_id: string
          project_title: string
          project_url?: string | null
          budget: number
          deadline_days: number
          message?: string | null
          status?: string | null
          sent_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          project_id?: string
          project_title?: string
          project_url?: string | null
          budget?: number
          deadline_days?: number
          message?: string | null
          status?: string | null
          sent_at?: string | null
        }
        Relationships: []
      }
      proposal_templates: {
        Row: {
          id: number
          user_id: string
          name: string
          content: string
          default_budget: number | null
          default_deadline_days: number | null
          is_default: boolean | null
          created_at: string | null
          updated_at: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          name: string
          content: string
          default_budget?: number | null
          default_deadline_days?: number | null
          is_default?: boolean | null
          created_at?: string | null
          updated_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          name?: string
          content?: string
          default_budget?: number | null
          default_deadline_days?: number | null
          is_default?: boolean | null
          created_at?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      saved_filters: {
        Row: {
          id: number
          user_id: string
          name: string
          filters_json: Json
          created_at: string | null
        }
        Insert: {
          id?: number
          user_id?: string
          name: string
          filters_json: Json
          created_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          name?: string
          filters_json?: Json
          created_at?: string | null
        }
        Relationships: []
      }
    }
    Views: { [_ in never]: never }
    Functions: { [_ in never]: never }
    Enums: { [_ in never]: never }
    CompositeTypes: { [_ in never]: never }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">
type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<T extends keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])> =
  (DefaultSchema["Tables"] & DefaultSchema["Views"])[T] extends { Row: infer R } ? R : never

export type TablesInsert<T extends keyof DefaultSchema["Tables"]> =
  DefaultSchema["Tables"][T] extends { Insert: infer I } ? I : never

export type TablesUpdate<T extends keyof DefaultSchema["Tables"]> =
  DefaultSchema["Tables"][T] extends { Update: infer U } ? U : never

export type Enums<T extends keyof DefaultSchema["Enums"]> = DefaultSchema["Enums"][T]

export type CompositeTypes<T extends keyof DefaultSchema["CompositeTypes"]> =
  DefaultSchema["CompositeTypes"][T]

export const Constants = { public: { Enums: {} } } as const
