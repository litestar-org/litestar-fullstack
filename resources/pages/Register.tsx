import { toast } from "@/components/ui/use-toast";
import MainLayout from "@/layouts/MainLayout";
import { registerUserService } from "@/services/authService";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const RegisterForm = () => {
  const navigate = useNavigate();
  const [data, setData] = useState({ name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      if (data.password.length < 6) {
        return toast({
          title: "Password is required!",
        });
      }
      setLoading(true);
      const { success, message } = await registerUserService(data);
      setLoading(false);
      if (success) {
        toast({
          title: message,
        });
        return navigate("/login");
      } else {
        return toast({
          title: message,
        });
      }
    } catch (error: any) {
      setLoading(false);
      console.log(error);
      toast({
        title: error.response.data.message,
      });
    }
  };

  return (
    <MainLayout
      title="Litestar Application - User Registration"
      description="Litestar Application - Register"
      keywords="register"
    >
      <section>
        <div className="w-full h-screen flex items-center justify-center px-4 py-10 sm:px-6 sm:py-16 lg:px-8 lg:py-24">
          <div className="xl:mx-auto xl:w-full xl:max-w-sm 2xl:max-w-md">
            <h2 className="text-center text-2xl font-bold leading-tight text-black">
              Sign up
            </h2>
            <p className="mt-2 text-center text-base text-gray-600">
              Already have an account?{" "}
              <Link
                to="/login"
                className="font-medium text-black transition-all duration-200 hover:underline"
              >
                Sign In
              </Link>
            </p>
            <form onSubmit={(e) => handleRegister(e)} className="mt-8">
              <div className="space-y-5">
                <div>
                  <label
                    htmlFor="name"
                    className="text-base font-medium text-gray-900"
                  >
                    {" "}
                    Full Name{" "}
                  </label>
                  <div className="mt-2">
                    <input
                      className="flex h-10 w-full rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={loading}
                      id="name"
                      name="name"
                      type="name"
                      placeholder="Enter your name."
                      autoComplete="name"
                      onChange={(e) =>
                        setData({ ...data, name: e.target.value })
                      }
                      required
                    ></input>
                  </div>
                </div>
                <div>
                  <label
                    htmlFor="email"
                    className="text-base font-medium text-gray-900"
                  >
                    {" "}
                    Email address{" "}
                  </label>
                  <div className="mt-2">
                    <input
                      className="flex h-10 w-full rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={loading}
                      id="email"
                      name="email"
                      type="email"
                      placeholder="Enter your email."
                      autoComplete="email"
                      onChange={(e) =>
                        setData({ ...data, email: e.target.value })
                      }
                      required
                    ></input>
                  </div>
                </div>
                <div>
                  <div className="flex items-center justify-between">
                    <label
                      htmlFor="password"
                      className="text-base font-medium text-gray-900"
                    >
                      {" "}
                      Password{" "}
                    </label>
                  </div>
                  <div className="mt-2">
                    <input
                      className="flex h-10 w-full rounded-md border border-gray-300 bg-transparent px-3 py-2 text-sm placeholder:text-gray-400 focus:outline-none focus:ring-1 focus:ring-gray-400 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50"
                      disabled={loading}
                      id="password"
                      name="password"
                      type="password"
                      placeholder="Enter your password."
                      autoComplete="current-password"
                      onChange={(e) =>
                        setData({ ...data, password: e.target.value })
                      }
                      required
                    ></input>
                  </div>
                </div>
                {data?.password && data.password.length < 6 && (
                  <p className="text-xs text-red-500 mt-2">
                    password must be 6 characters long.
                  </p>
                )}

                <div>
                  <button
                    disabled={loading}
                    type="submit"
                    className="inline-flex w-full items-center justify-center rounded-md bg-black px-3.5 py-2.5 font-semibold leading-7 text-white hover:bg-black/80 transition-transform active:scale-[98%]"
                  >
                    {loading ? "Creating account.." : " Create Account"}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </section>
    </MainLayout>
  );
};

export default RegisterForm;
