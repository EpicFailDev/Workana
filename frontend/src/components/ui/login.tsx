"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, Eye, EyeOff } from "lucide-react";
import styles from "./login.module.css";

// Validation schema for the form
const formSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email." }),
  password: z
    .string()
    .min(8, { message: "Password must be at least 8 characters." }),
  rememberMe: z.boolean().default(false).optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface AuthFormSplitScreenProps {
  logo: React.ReactNode;
  title: React.ReactNode;
  description: string;
  imageSrc: string;
  imageAlt: string;
  onSubmit: (data: FormValues) => Promise<void>;
  forgotPasswordHref: string;
  createAccountHref: string;
  footerLabelText?: string;
  footerLinkText?: string;
  showRememberMe?: boolean;
  onGoogleClick?: () => void;
}

export function AuthFormSplitScreen({
  logo,
  title,
  description,
  imageSrc,
  imageAlt,
  onSubmit,
  forgotPasswordHref,
  createAccountHref,
  footerLabelText = "Don't have an account?",
  footerLinkText = "Create one",
  showRememberMe = true,
  onGoogleClick,
}: AuthFormSplitScreenProps) {
  const [isLoading, setIsLoading] = React.useState(false);
  const [showPassword, setShowPassword] = React.useState(false);
  const [currentImage, setCurrentImage] = React.useState(imageSrc);

  React.useEffect(() => {
    setCurrentImage(imageSrc);
  }, [imageSrc]);

  const handleImageError = () => {
    if (currentImage !== "/login_bg.png") {
      setCurrentImage("/login_bg.png");
    }
  };

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  });

  const handleFormSubmit = async (data: FormValues) => {
    setIsLoading(true);
    try {
      await onSubmit(data);
    } catch (error) {
      console.error("Submission failed:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Animation variants for staggering children
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

  return (
    <div className={styles.screen}>
      {/* Left Panel: Form */}
      <div className={styles.leftPanel}>
        {/* Subtle background ambient lights */}
        <div className={styles.formShell}>
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="flex flex-col"
          >
            <motion.div variants={itemVariants} className={styles.logoBlock}>
              {logo}
            </motion.div>
            
            <motion.div variants={itemVariants} className={styles.header}>
              {title}
              <p className={styles.description}>{description}</p>
            </motion.div>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(handleFormSubmit)}
                className={styles.form}
              >
                <motion.div variants={itemVariants}>
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem className={styles.field}>
                        <FormLabel className={styles.label}>Email address</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="you@example.com"
                            {...field}
                            disabled={isLoading}
                            autoComplete="email"
                            className={styles.input}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </motion.div>

                <motion.div variants={itemVariants}>
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem className={styles.field}>
                        <FormLabel className={styles.label}>Password</FormLabel>
                        <FormControl>
                          <div className={styles.passwordWrap}>
                            <Input
                              type={showPassword ? "text" : "password"}
                              placeholder="••••••••••••"
                              {...field}
                              disabled={isLoading}
                              autoComplete={showRememberMe ? "current-password" : "new-password"}
                              className={`${styles.input} ${styles.passwordInput}`}
                            />
                            <button
                              type="button"
                              onClick={() => setShowPassword(!showPassword)}
                              className={styles.eyeButton}
                              disabled={isLoading}
                              aria-label={showPassword ? "Hide password" : "Show password"}
                            >
                              {showPassword ? (
                                <EyeOff className="h-4.5 w-4.5" />
                              ) : (
                                <Eye className="h-4.5 w-4.5" />
                              )}
                            </button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </motion.div>

                {showRememberMe && (
                  <motion.div
                    variants={itemVariants}
                    className="flex items-center justify-between pt-0.5"
                  >
                    <FormField
                      control={form.control}
                      name="rememberMe"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-center space-x-2 space-y-0">
                          <FormControl>
                            <Checkbox
                              checked={field.value}
                              onCheckedChange={field.onChange}
                              disabled={isLoading}
                              className="h-5 w-5 rounded-[5px] border-[#5b5e68] data-[state=checked]:border-[#1478ff] data-[state=checked]:bg-[#1478ff]"
                            />
                          </FormControl>
                          <div className="leading-none">
                            <FormLabel className="cursor-pointer select-none text-[13px] font-normal text-[#a6a8b2]">
                              Remember me
                            </FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />
                    <a
                      href={forgotPasswordHref}
                      className="text-[13px] text-[#b7b8bf] transition-colors hover:text-white hover:underline"
                    >
                      Forgot password?
                    </a>
                  </motion.div>
                )}

                <motion.div variants={itemVariants} className="pt-3">
                  <Button 
                    type="submit" 
                    className="h-[54px] w-full rounded-lg bg-gradient-to-r from-[#ff5a0a] via-[#e928bd] to-[#087cff] text-[15px] font-semibold text-white shadow-[0_8px_28px_rgba(37,74,210,0.2)] transition-all hover:brightness-110 active:scale-[0.99]" 
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : null}
                    Continue
                  </Button>
                </motion.div>
              </form>
            </Form>

            {onGoogleClick && (
              <motion.div variants={itemVariants} className="w-full">
                {/* Divider */}
                <div className="flex items-center my-6">
                  <div className="flex-1 h-[1px] bg-white/5" />
                  <span className="text-xs text-slate-500 uppercase tracking-widest px-3">
                    Ou acesse com
                  </span>
                  <div className="flex-1 h-[1px] bg-white/5" />
                </div>

                {/* Google Button */}
                <Button
                  type="button"
                  onClick={onGoogleClick}
                  disabled={isLoading}
                  className="w-full h-12 bg-white/5 hover:bg-white/10 text-white border border-white/10 hover:border-white/20 font-medium rounded-xl transition-all flex items-center justify-center gap-3 active:scale-[0.99] border-none"
                >
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                    />
                  </svg>
                  Google
                </Button>
              </motion.div>
            )}

            <motion.p
              variants={itemVariants}
              className="mt-10 text-center text-[16px] text-[#a6a8b2]"
            >
              {footerLabelText}{" "}
              <a
                href={createAccountHref}
                className="font-semibold text-white transition-all hover:underline"
              >
                {footerLinkText}
              </a>
            </motion.p>
          </motion.div>
        </div>
      </div>

      {/* Right Panel: Image */}
      <div className={styles.rightPanel}>
        <img
          src={currentImage}
          alt={imageAlt}
          className="h-full w-full object-cover"
          onError={handleImageError}
        />
      </div>
    </div>
  );
}
