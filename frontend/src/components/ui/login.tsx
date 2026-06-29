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
      <div className={styles.rightPanel} />
    </div>
  );
}
